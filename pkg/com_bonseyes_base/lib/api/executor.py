from abc import ABCMeta, abstractmethod
from typing import Dict, Union, Optional, List

from . import workflow as workflow_api

from .context import Context
from .runtime import Instance, ApplicationConfig, Runtime
from .storage import StorableObject
from .utils import NamedObject, NamedObjectMap, OrderedNamedObjectList, OrderedNamedObject
from .values import Value, Argument


class ExecutionAlreadyExists(Exception):
    pass


class WorkerStatus:
    PENDING = 'pending'
    CREATED = 'created'


class InvalidWorkerStatusException(Exception):
    pass


class Worker(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def worker_description(self) -> 'workflow_api.WorkerDescription':
        pass

    @property
    @abstractmethod
    def instance(self) -> Instance:
        pass

    @abstractmethod
    def create_instance(self) -> None:
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        pass


class StepStatus:
    PENDING = 'pending'
    IN_PROGRESS = 'in-progress'
    COMPLETED = 'completed'
    SUSPENDED = 'suspended'
    FAILED = 'failed'


class StepFailedException(Exception):
    pass


class Step(OrderedNamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def step_description(self) -> 'workflow_api.StepDescription':
        pass

    @abstractmethod
    def execute(self) -> None:
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        pass


class ExecutionStatus:
    PENDING = 'pending'
    IN_PROGRESS = 'in-progress'
    SUSPENDED = 'suspended'
    COMPLETED = 'completed'
    FAILED = 'failed'


class SourceStatus:
    PENDING = 'pending'
    CREATED = 'created'


class Source(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def instance(self) -> Instance:
        pass

    @property
    @abstractmethod
    def source_description(self) -> 'SourceDescription':
        pass

    @abstractmethod
    def create_instance(self) -> None:
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        pass


class OutputStatus:
    PENDING = "pending"
    ASSIGNED = "assigned"


class Output(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def output_description(self) -> 'workflow_api.OutputDescription':
        pass

    @property
    @abstractmethod
    def worker_name(self) -> str:
        pass

    @property
    @abstractmethod
    def artifact_name(self) -> Union[str, None]:
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        pass


class Execution(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def workflow(self) -> 'workflow_api.Workflow':
        pass

    @property
    @abstractmethod
    def workers(self) -> NamedObjectMap[Worker]:
        pass

    @property
    @abstractmethod
    def sources(self) -> NamedObjectMap[Source]:
        pass

    @property
    @abstractmethod
    def steps(self) -> OrderedNamedObjectList[Step]:
        pass

    @property
    @abstractmethod
    def config(self) -> 'ExecutionConfig':
        pass

    @property
    @abstractmethod
    def arguments(self) -> NamedObjectMap[Argument]:
        pass

    @property
    @abstractmethod
    def outputs(self) -> NamedObjectMap[Output]:
        pass

    @property
    @abstractmethod
    def context(self) -> Context:
        pass

    @property
    @abstractmethod
    def default_runtime_url(self) -> str:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def retry(self, step_index: Optional[int]=None,
              update_workflow: 'Optional[workflow_api.Workflow]' = None,
              recreate_workers: Optional[List[str]]=None,
              update_context: Optional[Context]=None) -> None:
        """ Retry to execute the workflow starting from step_index or the last step that failed"""
        pass

    @property
    @abstractmethod
    def current_step(self) -> Optional[Step]:
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        pass

    @abstractmethod
    def delete(self) -> None:
        pass


class SourceDescription(StorableObject):

    def __init__(self, data: Dict[str, str]) -> None:
        self._data = data

    @property
    def executor_url(self) -> str:
        return self._data.get('executor_url')

    @property
    def execution(self) -> str:
        return self._data.get('execution')

    @property
    def worker(self) -> str:
        return self._data.get('worker')

    def to_dict(self) -> Dict[str, str]:
        return self._data


class ExecutionConfig(metaclass=ABCMeta):

    @property
    @abstractmethod
    def runtime(self) -> Runtime:
        pass

    @property
    @abstractmethod
    def runtime_url(self) -> str:
        pass

    @property
    @abstractmethod
    def application_config(self) -> ApplicationConfig:
        pass

    @property
    @abstractmethod
    def environment(self) -> Dict[str, str]:
        pass


class Executor(metaclass=ABCMeta):

    @abstractmethod
    def create_execution(self, name: str, workflow: 'workflow_api.Workflow', context: Context,
                         config: ExecutionConfig, arguments: Dict[str, Value],
                         sources: Dict[str, SourceDescription]) -> Execution:
        pass

    @abstractmethod
    def get_execution_from_url(self, url: str) -> Execution:
        pass

    @property
    @abstractmethod
    def executions(self) -> NamedObjectMap[Execution]:
        pass

    @abstractmethod
    def parse_config(self, data: Dict):
        pass
