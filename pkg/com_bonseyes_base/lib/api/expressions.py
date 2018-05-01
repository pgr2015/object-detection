import json
from typing import Callable
from typing import Dict, Any, Optional
from typing import List

from abc import ABCMeta, abstractmethod

from . import executor as executor_api

from .tool import get_tool_from_url
from .values import Value
from ..impl.values.memory_values import StringValueFromMemory, PlainObjectValueFromMemory, \
    ResourceValueFromMemory, \
    UrlValueFromMemory

OPERATION_TYPES = {}  # type: Dict[str, Callable[..., 'Expression']]


class Expression(metaclass=ABCMeta):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        self._data = data
        self._parent = parent

    @abstractmethod
    def as_value(self, execution: 'executor_api.Execution') -> Value:
        pass

    def create_sub_expression(self, data: Any) -> 'Expression':
        return create_expression(data, self)

    def validate(self):
        pass


class String(Expression):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        super().__init__(parent, data)

        if not isinstance(data, str):
            raise ValueError('Unsupported type' + str(type(data)))

    def as_value(self, execution: 'executor_api.Execution') -> Value:
        return StringValueFromMemory(self._data)


OPERATION_TYPES['string'] = String


class Map(Expression):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        super().__init__(parent, data)

        if not isinstance(data, dict):
            raise ValueError('Unsupported type' + str(type(data)))

        self._map = {}  # type: Dict[str, Expression]

        for key, value in data.items():
            self._map[key] = self.create_sub_expression(value)

    def as_value(self, execution: 'executor_api.Execution') -> Value:
        return PlainObjectValueFromMemory({key: entry.as_value(execution).as_plain_object().get()
                                           for key, entry in self._map.items()})


OPERATION_TYPES['map'] = Map


class Array(Expression):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        super().__init__(parent, data)

        if not isinstance(data, list):
            raise ValueError('Unsupported type' + str(type(data)))

        self._array = []  # type: List[Expression]

        for value in data:
            self._array.append(self.create_sub_expression(value))

    def as_value(self, execution: 'executor_api.Execution') -> Value:
        return PlainObjectValueFromMemory([entry.as_value(execution).as_plain_object().get()
                                           for entry in self._array])


OPERATION_TYPES['array'] = Array


class WorkflowParameter(Expression):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        super().__init__(parent, data)

        if not isinstance(data, dict):
            raise ValueError('Unsupported type' + str(type(data)))

        if 'name' not in data:
            raise Exception("Missing name in " + json.dumps(data))

        self._name = self.create_sub_expression(data['name'])

    def as_value(self, execution: 'executor_api.Execution') -> Value:

        name = self._name.as_value(execution).as_string().get()

        if name not in execution.workflow.parameters.names:
            raise Exception("Execution has no parameter " + name +
                            " referenced in " + json.dumps(self._data))

        return execution.arguments.get(name).value


OPERATION_TYPES['workflow-parameter'] = WorkflowParameter


class WorkflowContextFile(Expression):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        super().__init__(parent, data)

        if not isinstance(data, dict):
            raise ValueError('Unsupported type' + str(type(data)))

        if 'name' not in data:
            raise Exception("Missing name in " + json.dumps(data))

        self._name = self.create_sub_expression(data['name'])

    def as_value(self, execution: 'executor_api.Execution') -> Value:
        name = self._name.as_value(execution).as_string().get()

        with execution.context.get_entry(name).open() as fp:
            return ResourceValueFromMemory(data=fp.read())  # type: ignore


OPERATION_TYPES['workflow-context-file'] = WorkflowContextFile


class EnvironmentValue(Expression):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        super().__init__(parent, data)

        if not isinstance(data, dict):
            raise ValueError('Unsupported type' + str(type(data)))

        if 'name' not in data:
            raise Exception("Missing name in " + json.dumps(data))

        self._name = self.create_sub_expression(data['name'])

    def as_value(self, execution: 'executor_api.Execution') -> Value:
        name = self._name.as_value(execution).as_string().get()

        if name not in execution.config.environment:
            raise Exception("Environment has no entry " + name +
                            " referenced in " + json.dumps(self._data))

        return PlainObjectValueFromMemory(execution.config.environment[name])


OPERATION_TYPES['environment'] = EnvironmentValue


class ArtifactUrl(Expression):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        super().__init__(parent, data)

        if not isinstance(data, dict):
            raise ValueError('Unsupported type' + str(type(data)))

        if 'step' in data:
            self._step_name = self.create_sub_expression(data['step'])
        else:
            self._step_name = None

            if 'worker' not in data:
                raise Exception("Missing worker parameter in " + json.dumps(data))

            if 'name' not in data:
                raise Exception("Missing name parameter in " + json.dumps(data))

            self._worker_name = self.create_sub_expression(data['worker'])
            self._artifact_name = self.create_sub_expression(data['name'])

        self._part = self.create_sub_expression(data.get('part', 'data'))
        self._path = self.create_sub_expression(data.get('path', ''))

    def as_value(self, execution: 'executor_api.Execution') -> Value:

        if self._step_name is not None:

            step_name = self._step_name.as_value(execution).as_string().get()

            try:
                step = execution.steps.get_by_name(step_name)
            except KeyError:
                raise Exception("Step referenced by " + json.dumps(self._data) + " doesn't exist")

            worker_name = step.step_description.worker_name
            artifact_name = step.step_description.artifact_name

        else:

            worker_name = self._worker_name.as_value(execution).as_string().get()
            artifact_name = self._artifact_name.as_value(execution).as_string().get()

        try:
            worker = execution.workers.get(worker_name)
        except KeyError:
            raise Exception("Worker referenced by " + json.dumps(self._data) + " doesn't exist")

        try:
            artifact = get_tool_from_url(worker.instance.url).artifacts.get(artifact_name)
        except KeyError:
            raise Exception("Worker " + worker_name + " has no artifact " + artifact_name +
                            " referenced in " + json.dumps(self._data))

        part = self._part.as_value(execution).as_string().get()

        if part == 'artifact':
            return UrlValueFromMemory(artifact.url)

        if part == 'data':
            path = self._path.as_value(execution).as_string().get()
            return UrlValueFromMemory(artifact.url + 'data/' + path)

        raise Exception("Unsupported part " + part + " referenced in " + json.dumps(self._data))


OPERATION_TYPES['artifact'] = ArtifactUrl


class WorkerUrl(Expression):

    def __init__(self, parent: Optional['Expression'], data: Any) -> None:
        super().__init__(parent, data)

        if not isinstance(data, dict):
            raise ValueError('Unsupported type' + str(type(data)))

        if 'name' not in data:
            raise Exception("Missing name in " + json.dumps(data))

        self._name = self.create_sub_expression(data['name'])

        self._path = self.create_sub_expression(data.get('path', ''))

    def as_value(self, execution: 'executor_api.Execution') -> Value:
        worker_name = self._name.as_value(execution).as_string().get()

        try:
            worker = execution.workers.get(worker_name)
        except KeyError:
            raise Exception("Execution has no worker " + worker_name +
                            " referenced in " + json.dumps(self._data))

        path = self._path.as_value(execution).as_string().get()

        return UrlValueFromMemory(worker.instance.url + path)


OPERATION_TYPES['worker-url'] = WorkerUrl


def create_expression(data: Any, parent: Optional[Expression]=None) -> 'Expression':
    if isinstance(data, Dict):
        if 'type' in data:
            return OPERATION_TYPES[data['type']](parent, data)
        else:
            return Map(parent, data)
    elif isinstance(data, str):
        return String(parent, data)
    elif isinstance(data, list):
        return Array(parent, data)
    else:
        raise ValueError('Unsupported type of data ' + str(type(data)))
