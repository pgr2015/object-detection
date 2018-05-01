import logging
from typing import Dict, Union, Optional, List

import os

from com_bonseyes_base.lib.api.tool import UnavailableToolException
from ..values.file_values import put_value_to_storage, StoredArgument
from ..runtime.simple_runtime import SimpleRuntime
from ..values.memory_values import UrlValueFromMemory, ResourceValueFromMemory, ArchiveValueFromUrl

from ...api import workflow as workflow_api

from ...api.context import StoredContext
from ...api.executor import Step, Worker, Execution, Executor, ExecutionAlreadyExists, \
    Context, StepStatus, WorkerStatus, ExecutionStatus, Source, SourceDescription, \
    SourceStatus, Output, OutputStatus, ExecutionConfig, StepFailedException
from ...api.runtime import Instance, Runtime, Application, DockerFromImageConfig, DockerFromContainerConfig, \
    ExistingInstanceImageConfig, ApplicationConfig, ManifestImageConfig
from ...api.storage import Storage, StoredNamedObject, StoredOrderedNamedObject, StoredOrderedNamedObjectList, \
    StoredNamedObjectMap, StoredStringField, StoredIntField, StoredObjectField, StorableObject
from ...api.tool import get_tool_from_url, ArtifactStatus, CommandFailedException
from ...api.utils import NamedObjectMap, OrderedNamedObjectList
from ...api.values import Value, ValueType, UrlValue, ResourceValue, ArchiveValue
from ...api.workflow import Workflow, WorkerDescription, StepDescription, OutputDescription
from ..storage.file_storage import FileStorage


class ExecutorNotFoundException(Exception):
    pass


class RuntimeNotFoundException(Exception):
    pass


def get_runtime(url: str) -> Runtime:
    if url == 'local:':
        from com_bonseyes_base.lib.impl.runtime.simple_runtime import SimpleRuntime
        runtime_dir = os.environ.get('BONSEYES_RUNTIME_DIR', os.path.expanduser('~/.bonseyes/runtime'))
        return SimpleRuntime(FileStorage(runtime_dir))
    else:
        raise RuntimeNotFoundException("Unsupported runtime " + url)


def get_executor(url: str) -> Executor:
    if url == 'local:':

        executor_path = os.environ.get('BONSEYES_EXECUTOR_DIR', os.path.expanduser('~/.bonseyes/executor'))
        return SimpleExecutor(FileStorage(executor_path))
    else:
        raise ExecutorNotFoundException("Unsupported executor " + url)


def is_source_url(url: str) -> bool:
    return url.startswith('source+http://')


def resolve_source_url(url: str, execution: 'Execution'):
    url = url[len('source+http://'):]

    path = url[url.index('/'):]
    source_name = url[:url.index('/')]

    return execution.sources.get(source_name).instance.url + path


def get_execution(url: str) -> Execution:
    if url.startswith('local:'):
        return get_executor('local:').get_execution_from_url(url)
    else:
        raise Exception("Unsupported execution " + url)


class InstanceReference:
    def __init__(self, storage):
        self._storage = storage

        self._runtime_url = StoredStringField(storage, 'runtime', required=True)
        self._application_name = StoredStringField(storage, 'application', required=True)
        self._instance_name = StoredStringField(storage, 'instance', required=True)

    def set(self, instance: Instance):
        self._runtime_url.set(instance.application.runtime.url)
        self._application_name.set(instance.application.name)
        self._instance_name.set(instance.name)

    @property
    def runtime(self) -> Runtime:
        return get_runtime(self._runtime_url.get())

    @property
    def application(self) -> Application:
        return self.runtime.applications.get(self._application_name.get())

    @property
    def instance(self) -> Instance:
        return self.application.instances.get(self._instance_name.get())


class SimpleWorker(Worker, StoredNamedObject):
    def __init__(self, execution: 'SimpleExecution', storage: Storage) -> None:
        StoredNamedObject.__init__(self, storage)
        self._execution = execution
        self._instance_reference = InstanceReference(storage)

        self._status = StoredStringField(storage, 'status', required=True)

    @property
    def worker_description(self) -> WorkerDescription:
        return self._execution.workflow.workers.get(self.name)

    def create(self) -> None:
        self._status.set(WorkerStatus.PENDING)

    @property
    def instance(self) -> Instance:
        return self._instance_reference.instance

    def create_instance(self) -> None:
        if self._storage.exists('/tool_instance'):
            raise Exception('Tool instance already created')

        data = self.worker_description.expression.as_value(self._execution).as_plain_object().get()

        app = self._execution.application

        environment = data.get('environment', {})

        logging.info("worker " + self.name + ": Creating tool instance")

        manifest_path = data['manifest']

        image = app.create_image(ManifestImageConfig(manifest_path))

        instance = app.create_instance(self.name, DockerFromImageConfig(image.name, environment))

        try:
            get_tool_from_url(instance.url).wait_until_online()
        except UnavailableToolException:
            with instance.open_log() as fp:
                raise UnavailableToolException("Error while starting tool. Logs:\n" + fp.read().decode('utf-8'))

        self._instance_reference.set(instance)
        self._status.set(WorkerStatus.CREATED)

    @property
    def status(self) -> str:
        return self._status.get()

    def recreate_instance(self) -> None:
        if self.status == WorkerStatus.PENDING:
            raise Exception('Worker %s never started' % self.name)

        self.instance.delete()
        self.create_instance()

    def delete(self):

        if self.status != WorkerStatus.PENDING:

            logging.info("worker " + self.name + ": Deleting")

            try:
                self.instance.delete()
            except KeyError:
                logging.error("Instance disappeared")

            # delete the application if it has been created just for this worker
            if self._execution.default_runtime_url != self._instance_reference.runtime.url and \
               self._execution.application.name != self._instance_reference.application.name:

                try:
                    self._instance_reference.application.delete()
                except KeyError:
                    logging.error("Application disappeared")

        self._storage.delete('/')


class SimpleSource(Source, StoredNamedObject):
    def __init__(self, execution: 'SimpleExecution', storage: Storage) -> None:
        StoredNamedObject.__init__(self, storage)
        self._execution = execution
        self._instance_reference = InstanceReference(storage)

        self._status = StoredStringField(storage, 'status', required=True)
        self._source_description = StoredObjectField(storage, 'description', SourceDescription, required=True)

    def create(self, description: SourceDescription):
        self._source_description.set(description)
        self._status.set(SourceStatus.PENDING)

    @property
    def instance(self) -> Instance:
        return self._instance_reference.instance

    @property
    def status(self) -> str:
        return self._status.get()

    @property
    def source_description(self) -> SourceDescription:
        return self._source_description.get()

    def create_instance(self) -> None:

        logging.info("source " + self.name + ": Creating tool instance from previous execution")

        executor = get_executor(self.source_description.executor_url)
        execution = executor.executions.get(self.source_description.execution)
        worker = execution.workers.get(self.source_description.worker)

        base_instance = worker.instance

        app = base_instance.application.runtime.create_application()

        image = app.create_image(ExistingInstanceImageConfig(base_instance.application.name,
                                                             base_instance.name))

        instance = app.create_instance(self.name,
                                       DockerFromContainerConfig(base_instance.application.name,
                                                                 base_instance.name, image.name))

        get_tool_from_url(instance.url).wait_until_online()
        self._instance_reference.set(instance)

        self._status.set(SourceStatus.CREATED)

    def delete(self):

        if self.status != WorkerStatus.PENDING:

            logging.info("source " + self.name + ": Deleting")

            try:
                self.instance.delete()
            except KeyError:
                logging.error("Instance disappeared")

            try:
                self._instance_reference.application.delete()
            except KeyError:
                logging.error("Application disappeared")

        self._storage.delete('/')


class SimpleOutput(StoredNamedObject, Output):
    def __init__(self, execution: 'SimpleExecution', storage: Storage):
        StoredNamedObject.__init__(self, storage)

        self._execution = execution

        self._status = StoredStringField(storage, 'status', required=True)
        self._worker_name = StoredStringField(storage, 'worker_name', required=True)
        self._artifact_name = StoredStringField(storage, 'artifact_name', required=False)

    def create(self):
        self._status.set(OutputStatus.PENDING)

    @property
    def output_description(self) -> OutputDescription:
        return self._execution.workflow.outputs.get(self.name)

    @property
    def worker_name(self) -> str:
        return self._worker_name.get()

    @property
    def artifact_name(self) -> Union[str, None]:
        return self._artifact_name.get()

    def set(self, worker_name: str, artifact_name: Union[str, None]) -> None:
        self._worker_name.set(worker_name)
        self._artifact_name.set(artifact_name)
        self._status.set(OutputStatus.ASSIGNED)

    @property
    def status(self) -> str:
        return self._status.get()


class SimpleStep(Step, StoredOrderedNamedObject):
    def __init__(self, execution: 'SimpleExecution', storage: Storage) -> None:
        StoredOrderedNamedObject.__init__(self, storage)
        self._storage = storage
        self._execution = execution
        self._status = StoredStringField(storage, 'status', required=True)

    def create(self) -> None:
        self._status.set(StepStatus.PENDING)
        self._name.set(self.step_description.name)

    def _assign_outputs(self):
        for assignment in self.step_description.outputs.all:
            output = self._execution.outputs.get(assignment.name)

            if assignment.step_name is not None:
                step = self._execution.steps.get_by_name(assignment.step_name).step_description
                output.set(step.worker_name, step.artifact_name)
            else:
                output.set(assignment.worker_name, assignment.artifact_name)

        if self.step_description.output is not None:
            output = self._execution.outputs.get(self.step_description.output)
            output.set(self.step_description.worker_name, self.step_description.artifact_name)

    def execute(self) -> None:

        try:
            logging.debug("step " + str(self.index) + ": Starting execution")

            if self.status == StepStatus.COMPLETED:
                logging.info("step " + str(self.index) + ": Finished execution, already completed")
                return

            step = self.step_description

            if step.is_wait:

                self._assign_outputs()

                if self.status == StepStatus.SUSPENDED:
                    logging.debug("step " + str(self.index) + ": Finished execution")
                    self._status.set(StepStatus.COMPLETED)
                else:
                    logging.debug("step " + str(self.index) + ": Suspending execution")
                    self._status.set(StepStatus.SUSPENDED)

                return

            self._status.set(StepStatus.IN_PROGRESS)

            worker = self._execution.workers.get(step.worker_name)

            tool = get_tool_from_url(worker.instance.url)

            manifest = tool.manifest

            parameters = {}

            logging.debug("step " + str(self.index) + ": Preparing arguments")

            for parameter in manifest.actions.get('create').parameters.all:

                if parameter.name not in step.arguments.names:

                    if parameter.optional:
                        continue
                    else:
                        raise Exception("Missing parameter " + parameter.name + " in step " + str(self.index))

                argument = step.arguments.get(parameter.name)

                value = argument.expression.as_value(self._execution)

                # resolve all urls that point to a source
                if isinstance(value, UrlValue):
                    if is_source_url(value.get()):
                        value = UrlValueFromMemory(resolve_source_url(value.get(), self._execution))

                # resolve all resources that point to a source
                if isinstance(value, ResourceValue):
                    if value.url is not None and is_source_url(value.url):
                        value = ResourceValueFromMemory(resolve_source_url(value.url, self._execution))

                # resolve all archives that point to a source
                if isinstance(value, ArchiveValue):
                    if value.url is not None and is_source_url(value.url):
                        value = ArchiveValueFromUrl(resolve_source_url(value.url, self._execution))

                # cast the value to what is expected by the tool
                if parameter.type == ValueType.PLAIN_OBJECT:
                    parameters[parameter.name] = value.as_plain_object()

                elif parameter.type == ValueType.STRING:
                    parameters[parameter.name] = value.as_string()

                elif parameter.type == ValueType.RESOURCE:
                    parameters[parameter.name] = value.as_resource()

                elif parameter.type == ValueType.ARCHIVE:
                    parameters[parameter.name] = value.as_archive()

                elif parameter.type == ValueType.URL:
                    parameters[parameter.name] = value.as_url()

            self._status.set(StepStatus.IN_PROGRESS)

            logging.debug("step " + str(self.index) + ": Starting artifact creation")

            command = tool.create_artifact(step.artifact_name, parameters)

            logging.debug("step " + str(self.index) + ": Waiting for completion")

            try:
                while command.artifact.status in [ArtifactStatus.PENDING, ArtifactStatus.IN_PROGRESS]:
                    tool.wait_for_completed(step.artifact_name)
            except CommandFailedException:
                raise StepFailedException('Failed to build artifact')

            if command.artifact.status != ArtifactStatus.COMPLETED:
                raise StepFailedException('Failed to build artifact')

            self._assign_outputs()

            self._status.set(StepStatus.COMPLETED)

            logging.debug("step " + str(self.index) + ": Execution completed")

        except StepFailedException:

            logging.info("step " + str(self.index) + ": Execution failed")

            self._status.set(StepStatus.FAILED)

        except:

            logging.info("step " + str(self.index) + ": Execution failed")

            self._status.set(StepStatus.FAILED)

            raise

    @property
    def step_description(self) -> StepDescription:
        return self._execution.workflow.steps.get_by_index(self.index)

    @property
    def status(self) -> str:
        return self._status.get()

    def clean(self) -> None:
        """ Discard artefact """

        self._status.set(StepStatus.PENDING)

        if self.step_description.is_wait:
            # Wait steps have no artefacts
            return

        worker = self._execution.workers.get(self.step_description.worker_name)
        tool = get_tool_from_url(worker.instance.url)

        if self.step_description.artifact_name in tool.artifacts.names:
            tool.delete_artifact(self.step_description.artifact_name)

    def delete(self):
        self._storage.delete()


class SimpleExecutionConfig(ExecutionConfig, StorableObject):
    def __init__(self, data: Dict):
        self._data = data

    @property
    def runtime(self) -> Runtime:
        return get_runtime(self.runtime_url)

    @property
    def runtime_url(self) -> str:
        return self._data.get('runtime_url', 'local:')

    @property
    def application_config(self) -> ApplicationConfig:
        return self.runtime.parse_application_config(self._data.get('application_config', {}))

    @property
    def environment(self) -> Dict[str, str]:
        return self._data.get('environment', {})

    def to_dict(self) -> Dict:
        return self._data


class SimpleExecutorStateException(Exception):
    pass


class SimpleExecution(Execution, StoredNamedObject):
    def __init__(self, executor: 'SimpleExecutor', storage: Storage) -> None:
        StoredNamedObject.__init__(self, storage)
        self._storage = storage
        self._executor = executor

        self._steps = StoredOrderedNamedObjectList(storage.get_substorage('steps'), lambda x: SimpleStep(self, x))
        self._workers = StoredNamedObjectMap(storage.get_substorage('workers'), lambda x: SimpleWorker(self, x))
        self._sources = StoredNamedObjectMap(storage.get_substorage('sources'), lambda x: SimpleSource(self, x))
        self._arguments = StoredNamedObjectMap(storage.get_substorage('arguments'), StoredArgument)
        self._outputs = StoredNamedObjectMap(storage.get_substorage('outputs'), lambda x: SimpleOutput(self, x))

        self._application_name = StoredStringField(storage, 'application', required=True)
        self._status = StoredStringField(storage, 'status', required=True)
        self._workflow = StoredObjectField(storage, 'workflow', Workflow, required=True)
        self._config = StoredObjectField(storage, 'config', SimpleExecutionConfig, required=True)
        self._current_step_index = StoredIntField(storage, 'current_step', required=False)

    @property
    def application(self) -> Application:

        try:
            runtime = get_runtime(self.default_runtime_url)
        except (RuntimeNotFoundException, ValueError):
            raise SimpleExecutorStateException("Cannot find runtime")

        try:
            return runtime.applications.get(self._application_name.get())
        except (KeyError, ValueError):
            raise SimpleExecutorStateException("Cannot find application")

    @property
    def workflow(self) -> Workflow:
        return self._workflow.get()

    @property
    def config(self) -> SimpleExecutionConfig:
        return self._config.get()

    def create(self,
               workflow: Workflow,
               config: Optional[ExecutionConfig] = None,
               context: Optional[Context] = None,
               arguments: Optional[Dict[str, Value]] = None,
               sources: Optional[Dict[str, SourceDescription]] = None) -> None:

        try:

            self._status.set(ExecutionStatus.PENDING)
            self._workflow.set(workflow)

            if config is None:
                config = SimpleExecutionConfig({})

            if not isinstance(config, SimpleExecutionConfig):
                raise ValueError("Invalid configuration type " + str(type(config)))

            self._config.set(config)

            # save the context

            logging.info("Saving context")

            context_storage = self._storage.get_substorage('/context')

            if context is not None:
                context.save_to_storage(context_storage)

            # save all the arguments

            logging.info("Saving arguments")

            if arguments is None:
                arguments = {}

            remaining_arguments = list(arguments.keys())

            arguments_substorage = self._storage.get_substorage('arguments')

            for parameter in workflow.parameters.all:

                try:
                    argument = arguments[parameter.name]
                except KeyError:
                    raise KeyError("Execution argument %s not found" % parameter.name)

                remaining_arguments.remove(parameter.name)

                storage = arguments_substorage.get_substorage(parameter.name)
                argument_obj = StoredArgument(storage)
                argument_obj.create(argument)

            if len(remaining_arguments) != 0:
                raise ValueError("Too many arguments %s" % str(remaining_arguments))

            logging.info("Creating internal state")

            # create all sources
            sources_substorage = self._storage.get_substorage('sources')

            if sources is None:
                sources = {}

            for name, description in sources.items():
                storage = sources_substorage.get_substorage(name)
                source = SimpleSource(self, storage)
                source.create(description)

            # create all steps
            steps_substorage = self._storage.get_substorage('steps')

            for idx, step in enumerate(self.workflow.steps.all):
                storage = steps_substorage.get_substorage(str(idx))
                SimpleStep(self, storage).create()

            # create all outputs
            outputs_substorage = self._storage.get_substorage('outputs')

            for output in self.workflow.outputs.all:
                storage = outputs_substorage.get_substorage(output.name)
                SimpleOutput(self, storage).create()

            # create all workers
            workers_substorage = self._storage.get_substorage('workers')

            for worker_description in self.workflow.workers.all:
                storage = workers_substorage.get_substorage(worker_description.name)
                SimpleWorker(self, storage).create()

            # creating an application
            logging.info("Creating application on runtime")
            runtime = get_runtime(self.default_runtime_url)
            application = runtime.create_application(self.context,
                                                     self.config.application_config)

            self._application_name.set(application.name)

        except:

            self._status.set(ExecutionStatus.FAILED)
            raise

    def add_output(self, name: str, value: Value):
        storage = self._storage.get_substorage('/outputs/' + name)
        put_value_to_storage(value, storage)

    @property
    def name(self) -> str:
        return self._storage.name

    @property
    def arguments(self) -> NamedObjectMap[StoredArgument]:
        return self._arguments

    @property
    def outputs(self) -> NamedObjectMap[SimpleOutput]:
        return self._outputs

    @property
    def workers(self) -> NamedObjectMap[SimpleWorker]:
        return self._workers

    @property
    def steps(self) -> OrderedNamedObjectList[SimpleStep]:
        return self._steps

    @property
    def sources(self) -> OrderedNamedObjectList[SimpleSource]:
        return self._sources

    @property
    def context(self) -> StoredContext:
        return StoredContext(self._storage.get_substorage('/context'))

    @property
    def default_runtime_url(self) -> str:
        return 'local:'

    @property
    def status(self) -> str:
        return self._status.get()

    @property
    def current_step(self) -> Optional[Step]:
        return self.steps.get_by_index(self._current_step_index.get())

    def execute(self) -> None:

        try:

            self._status.set(ExecutionStatus.IN_PROGRESS)

            for worker in self.workers.all:

                if worker.status != WorkerStatus.CREATED:
                    logging.info("Creating worker " + worker.name)
                    worker.create_instance()

            for source in self.sources.all:

                if source.status != SourceStatus.CREATED:
                    logging.info("Creating source " + source.name)
                    source.create_instance()

            for step in self.steps.all:

                self._current_step_index.set(step.index)

                if step.status == StepStatus.COMPLETED:
                    continue

                worker_name = step.step_description.worker_name if step.step_description.worker_name is not None else ""
                step_name = step.step_description.name if step.step_description.name is not None else ""
                logging.info("step#" + str(step.index) + " " + step_name +
                             " [" + worker_name + "]" + ": " + step.step_description.description)

                step.execute()

                if step.status == StepStatus.SUSPENDED:
                    logging.info("Execution suspended")
                    self._status.set(ExecutionStatus.SUSPENDED)
                    return

                if step.status == StepStatus.FAILED:
                    logging.info("Execution failed")
                    self._status.set(ExecutionStatus.FAILED)
                    return

            self._current_step_index.set(None)

            for source in self.sources.all:
                logging.info("Sopping source " + source.name)
                source.instance.stop()

            for worker in self.workers.all:
                logging.info("Stopping worker " + worker.name)
                worker.instance.stop()

            self._status.set(ExecutionStatus.COMPLETED)

        except:

            self._status.set(ExecutionStatus.FAILED)
            raise

    def retry(self, step_index: Optional[int] = None,
              update_workflow: Optional['workflow_api.Workflow'] = None,
              recreate_workers: Optional[List[str]] = None,
              update_context: Optional[Context] = None) -> None:
        if self._status.get() != ExecutionStatus.FAILED:
            raise Exception("Invalid state for retry: " + str(self._status.get()))

        if step_index is None:

            step = None

            # Find the step that failed
            for step in self.steps.all:
                if step.status != StepStatus.COMPLETED:
                    break

            if step is None:
                raise Exception("No steps found")

            if step.status == StepStatus.COMPLETED:
                raise Exception("No failed steps found")

            step_index = step.index
        else:
            # Check that the given step index is valid
            # Check that the previous steps succesfully completed
            for step in self.steps.all:
                if step.step_description.index >= step_index:
                    break
                if step.status != StepStatus.COMPLETED:
                    raise Exception("Step %d not completed succesfully" % step.step_description.index)
            if step_index > self.steps.count:
                raise Exception("Invalid step number specified: %d" % step_index)

        if update_workflow is not None:
            # @TODO Not yet implemented
            # Note: worker, output and parameter list are not updated here
            curr_workflow = self.workflow

            next_workflow_data = curr_workflow.to_dict()
            next_workflow_data['steps'] = update_workflow.to_dict()['steps']
            next_workflow = Workflow(next_workflow_data)

            self._workflow.set(next_workflow)

            steps_substorage = self._storage.get_substorage('steps')

            for step in self.workflow.steps.all:
                if step.index > curr_workflow.steps.count:
                    storage = steps_substorage.get_substorage(str(step.index))
                    SimpleStep(self, storage).create()

            for step in self.steps.all:
                if step.index > next_workflow.steps.count:
                    step.delete()

        if update_context is not None:
            logging.info("Saving new context")

            context_storage = self._storage.get_substorage('context')
            context_storage.delete('/')

            new_context_storage = self._storage.get_substorage('context')
            update_context.save_to_storage(new_context_storage)

            self.application.update_context(update_context)

        if recreate_workers is not None:
            for worker in recreate_workers:
                if worker in self.workers.names:
                    self.workers.get(worker).recreate_instance()
                else:
                    raise Exception("Worker %s doesn't exist in current execution" % worker)

        # Now throw away artefacts of steps from this one
        for step in self.steps.all:
            if step.step_description.index >= step_index:
                step.clean()

        # Now restart execution from current step
        self.execute()

    def delete(self) -> None:
        for worker in self.workers.all:
            worker.delete()

        for source in self.sources.all:
            source.delete()

        try:
            self.application.delete()
        except SimpleExecutorStateException:
            logging.info("Cannot find application information")

        self._storage.delete('/')


class SimpleExecutor(Executor):
    def __init__(self, storage: Storage) -> None:
        self._executions = StoredNamedObjectMap(storage.get_substorage('/executions'),
                                                lambda x: SimpleExecution(self, x))
        self._storage = storage

    def create_execution(self, name: str,
                         workflow: 'workflow_api.Workflow',
                         context: Context,
                         config: Optional[ExecutionConfig] = None,
                         arguments: Optional[Dict[str, Value]] = None,
                         sources: Optional[Dict[str, SourceDescription]] = None) -> SimpleExecution:
        if self._storage.exists('/executions/' + name):
            raise ExecutionAlreadyExists()

        logging.info("Creating execution " + name)

        self._storage.makedirs('/executions/' + name)

        execution = SimpleExecution(self, self._storage.get_substorage('/executions/' + name))
        execution.create(workflow, config, context, arguments, sources)

        return execution

    def get_execution_from_url(self, url: str) -> Execution:
        return self.executions.get(url[len("local:"):])

    @property
    def executions(self) -> NamedObjectMap[SimpleExecution]:
        return self._executions

    def parse_config(self, data: Dict):
        return SimpleExecutionConfig(data)
