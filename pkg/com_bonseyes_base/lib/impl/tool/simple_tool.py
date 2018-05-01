import logging
import time
from io import StringIO
from typing import IO, Dict

from abc import ABCMeta

from ...api.data import data_formats
from ...api.metrics import metric_formats
from ..utils import load_callable

from ...api.metadata import MetadataEditor, metadata_formats
from ...api.manifest import Manifest
from ...api.storage import StoredNamedObjectMap, StoredNamedObject, StoredOrderedNamedObjectList, \
    StoredStringField, StoredOrderedNamedObject, Storage
from ...api.tool import Tool, Artifact, MetricViewer, Command, DataViewer, DataEditor, \
    MetadataViewer, MetricEditor, ArtifactAlreadyExistsException, ArtifactStatus, Context
from ...api.utils import NamedObjectMap, OrderedNamedObjectList
from ...api.values import Value, ResourceValue, UrlValue, ArchiveValue, ValueType
from ..values.file_values import StoredArgument


class SimpleToolConfig:

    def __init__(self, data: Dict):
        self._data = data

    def get_function_for_action(self, action_name):
        return self._data.get('actions', {}).get(action_name, 'actions:' + action_name)


class SimpleTool(Tool, metaclass=ABCMeta):

    def __init__(self, storage: Storage, manifest: Manifest, config: SimpleToolConfig):
        self._storage = storage
        self._artifacts = StoredNamedObjectMap(self._storage, lambda x: StoredArtifact(self, x))
        self._config = config
        self._manifest = manifest

    @property
    def manifest(self) -> Manifest:
        return self._manifest

    @property
    def artifacts(self) -> NamedObjectMap['StoredArtifact']:
        return self._artifacts

    def wait_until_online(self, timeout: int=10):
        return

    def execute_action(self, artifact_name: str):

        artifact = self.artifacts.get(artifact_name)

        if artifact.status != ArtifactStatus.PENDING:
            return

        command = artifact.history.get_by_index(artifact.history.count - 1)

        # setup logging
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(command.edit_log())
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        edited_resources = []

        # noinspection PyBroadException
        try:

            artifact.set_status(ArtifactStatus.IN_PROGRESS)

            processing_function_name = self._config.get_function_for_action(command.action_name)
            processing_function = load_callable(processing_function_name)

            context = SimpleContext(command)

            kwargs = {}

            parameters = self.manifest.actions.get(command.action_name).parameters

            for argument in command.arguments.all:

                value = argument.value

                data_type = parameters.get(argument.name).data_format
                parameter_type = parameters.get(argument.name).type

                if data_type is not None:

                    format_obj = data_formats.get(data_type)

                    if parameter_type == ValueType.ARCHIVE:

                        if isinstance(value, ArchiveValue):

                            if value.url is None:
                                editor = value.get()
                                url = 'file://' + editor.open()
                                edited_resources.append(editor)
                            else:
                                url = value.url
                        else:
                            raise Exception("Received unsupported value for typed archive parameter")

                    elif parameter_type == ValueType.RESOURCE:

                        if isinstance(value, ResourceValue):

                            if value.url is None:
                                editor = value.edit()
                                url = 'file://' + editor.open()
                                edited_resources.append(editor)
                            else:
                                url = value.url
                        else:
                            raise Exception("Received unsupported value for typed resource parameter")

                    elif parameter_type == ValueType.URL:
                        if isinstance(value, UrlValue):
                            url = value.get()
                        else:
                            raise Exception("Received unsupported value for typed url parameter")
                    else:
                        raise Exception("Invalid typed value")

                    kwargs[argument.name] = format_obj.get_viewer(url)

                elif isinstance(value, ResourceValue):
                    editor = value.edit()
                    kwargs[argument.name] = editor.open()
                    edited_resources.append(editor)

                elif isinstance(value, ArchiveValue):
                    editor = value.get()
                    kwargs[argument.name] = editor.open()
                    edited_resources.append(editor)

                else:
                    kwargs[argument.name] = value.get()

            processing_function(context, **kwargs)

            artifact.set_status(ArtifactStatus.COMPLETED)

        except:

            ch.flush()

            logger.exception('Error while processing')
            artifact.set_status(ArtifactStatus.FAILED)

        finally:

            for edited_resource in edited_resources:
                edited_resource.close()

            ch.close()
            logger.removeHandler(ch)

    def _schedule_execution(self, artifact_name: str):
        self.execute_action(artifact_name)

    def create_artifact(self, artifact_name: str, arguments: Dict[str, Value]) -> Command:

        if self._artifacts.storage.exists(artifact_name):
            raise ArtifactAlreadyExistsException()

        artifact = StoredArtifact(self, self._artifacts.storage.get_substorage(artifact_name))

        command = artifact.create(arguments)

        self._schedule_execution(artifact_name)

        return command

    def modify_artifact(self, artifact_name: str, action_name: str, arguments: Dict[str, Value]) -> Command:
        artifact = self._artifacts.get(artifact_name)
        command = artifact.add_command(action_name, arguments)

        self._schedule_execution(artifact_name)

        return command

    def wait_for_completed(self, artifact_name: str) -> None:

        artifact = self._artifacts.get(artifact_name)
        while artifact.status in [ArtifactStatus.IN_PROGRESS, ArtifactStatus.PENDING]:
            time.sleep(1)

    def interrupt(self, artifact_name: str, command_index: int):
        self.artifacts.get(artifact_name).history.get_by_index(command_index).set_interrupt_requested()

    def delete_artifact(self, artifact_name: str):

        if self.artifacts.get(artifact_name).status == ArtifactStatus.IN_PROGRESS:
            raise Exception("Cannot delete artifact in progress")

        self._artifacts.storage.delete(artifact_name)

    @property
    def url(self) -> str:
        return 'local:'


class SimpleContext(Context):

    def __init__(self, command: 'StoredCommand'):
        self._command = command

    @property
    def data(self) -> DataEditor:
        return self._command.artifact.data_editor

    @property
    def metrics(self) -> NamedObjectMap[MetricEditor]:
        return self._command.metric_editors

    @property
    def interrupt_requested(self) -> bool:
        return self._command.interrupt_requested


class StoredArtifact(Artifact, StoredNamedObject):

    def __init__(self, tool: Tool, storage: Storage):
        StoredNamedObject.__init__(self, storage)
        self._tool = tool
        self._status = StoredStringField(storage, 'status')

        history_storage = self._storage.get_substorage('history')
        self._history = StoredOrderedNamedObjectList(history_storage, lambda x: StoredCommand(self, x))

    def create(self, arguments: Dict[str, Value]) -> Command:
        return self.add_command('create', arguments)

    def add_command(self, action_name: str, arguments: Dict[str, Value]) -> 'StoredCommand':

        if self.status in [ArtifactStatus.IN_PROGRESS, ArtifactStatus.PENDING]:
            raise Exception("Artifact already busy")

        self._status.set(ArtifactStatus.PENDING)

        command_storage = self._history.storage.get_substorage(str(self._history.count))

        command = StoredCommand(self, command_storage)
        command.create(action_name, arguments)

        return command

    def set_status(self, status: str):
        self._status.set(status)

    @property
    def tool(self) -> Tool:
        return self._tool

    @property
    def status(self) -> str:
        return self._status.get()

    @property
    def history(self) -> OrderedNamedObjectList['StoredCommand']:
        return self._history

    @property
    def data_editor(self) -> DataEditor:
        data_format = data_formats.get(self.tool.manifest.output_data_format)
        return data_format.get_editor(self.data_url)

    @property
    def metadata_editor(self) -> MetadataEditor:
        data_format = data_formats.get(self.tool.manifest.output_data_format)
        metdata_format = metadata_formats.get(data_format.metadata_type)
        return metdata_format.get_editor(self.metadata_url)

    @property
    def data(self) -> DataViewer:
        data_format = data_formats.get(self.tool.manifest.output_data_format)
        return data_format.get_viewer(self.data_url)

    @property
    def metadata(self) -> MetadataViewer:
        data_format = data_formats.get(self.tool.manifest.output_data_format)
        metdata_format = metadata_formats.get(data_format.metadata_type)
        return metdata_format.get_viewer(self.metadata_url)

    @property
    def data_url(self) -> str:
        return self._storage.url.rstrip('/') + '/data'

    @property
    def metadata_url(self) -> str:
        return self._storage.url.rstrip('/') + '/metadata'

    @property
    def url(self) -> str:
        return self._storage.url


class StoredCommand(Command, StoredOrderedNamedObject):

    def __init__(self, artifact: StoredArtifact, storage: Storage):
        StoredOrderedNamedObject.__init__(self, storage)
        self._artifact = artifact

        self._action_name = StoredStringField(storage, 'action')
        self._interrupt_requested = StoredStringField(storage, 'interrupt_requested')

        arguments_storage = storage.get_substorage('arguments')
        self._arguments = StoredNamedObjectMap(arguments_storage, StoredArgument)

        metrics_storage = storage.get_substorage('metrics')
        self._metrics = StoredNamedObjectMap(metrics_storage, self._get_metric)
        self._metric_editors = StoredNamedObjectMap(metrics_storage, self._get_metric_editors)

    def create(self, action_name: str, arguments: Dict[str, Value]):

        action_desc = self.artifact.tool.manifest.actions.get(action_name)

        self._action_name.set(action_name)
        self._interrupt_requested.set(str(False))

        for name, value in arguments.items():

            argument_storage = self._arguments.storage.get_substorage(name)
            StoredArgument(argument_storage).create(value)

        for metric_desc in action_desc.metrics.all:
            self._metrics.storage.get_substorage(metric_desc.name)

    def _get_metric(self, storage: Storage) -> MetricViewer:
        manifest = self.artifact.tool.manifest
        metric_desc = manifest.actions.get(self.action_name).metrics.get(storage.name)
        metric_format = metric_formats.get(metric_desc.metric_type)
        return metric_format.get_viewer(storage.url.rstrip('/') + '/data', storage.name)

    def _get_metric_editors(self, storage: Storage) -> MetricEditor:
        manifest = self.artifact.tool.manifest
        metric_desc = manifest.actions.get(self.action_name).metrics.get(storage.name)
        metric_format = metric_formats.get(metric_desc.metric_type)
        return metric_format.get_editor(storage.url.rstrip('/') + '/data', storage.name)

    @property
    def artifact(self) -> StoredArtifact:
        return self._artifact

    @property
    def arguments(self) -> NamedObjectMap[StoredArgument]:
        return self._arguments

    @property
    def action_name(self) -> str:
        return self._action_name.get()

    @property
    def metrics(self) -> NamedObjectMap[MetricViewer]:
        return self._metrics

    @property
    def metric_editors(self) -> NamedObjectMap[MetricEditor]:
        return self._metric_editors

    def open_log(self) -> IO[str]:

        if not self._storage.exists('log'):
            return StringIO()

        return self._storage.open('log', mode='r')

    def edit_log(self) -> IO[str]:
        return self._storage.open('log', mode='w')

    def set_interrupt_requested(self):
        self._interrupt_requested.set(str(True))

    @property
    def interrupt_requested(self) -> bool:
        return bool(self._interrupt_requested.get())
