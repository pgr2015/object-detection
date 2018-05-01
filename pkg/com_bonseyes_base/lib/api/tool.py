from typing import Dict, IO, Generic, TypeVar

import importlib
from abc import abstractmethod, ABCMeta

from .data import DataViewer, DataEditor
from .metadata import MetadataViewer
from .metrics import MetricEditor, MetricViewer
from .manifest import Manifest
from .utils import NamedObjectMap, OrderedNamedObjectList, OrderedNamedObject, NamedObject
from .values import Value, Argument


class UnavailableToolException(Exception):
    pass


class CommandFailedException(Exception):
    pass


class ToolException(Exception):
    pass


class ArtifactAlreadyExistsException(Exception):
    pass


class ArtifactStatus:
    COMPLETED = 'completed'
    IN_PROGRESS = 'in-progress'
    FAILED = 'failed'
    PENDING = 'pending'


class Tool(metaclass=ABCMeta):

    @property
    @abstractmethod
    def manifest(self) -> Manifest:
        pass

    @property
    @abstractmethod
    def artifacts(self) -> NamedObjectMap['Artifact']:
        pass

    @abstractmethod
    def wait_until_online(self, timeout: int=10):
        pass

    @abstractmethod
    def create_artifact(self, artifact_name: str, arguments: Dict[str, Value]) -> 'Command':
        pass

    @abstractmethod
    def modify_artifact(self, artifact_name: str, action_name: str, arguments: Dict[str, Value]) -> 'Command':
        pass

    @abstractmethod
    def wait_for_completed(self, artifact_name: str) -> None:
        pass

    @abstractmethod
    def interrupt(self, artifact_name: str, command_index: int):
        pass

    @abstractmethod
    def delete_artifact(self, artifact_name: str):
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass


class Artifact(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def tool(self) -> Tool:
        pass

    @property
    @abstractmethod
    def history(self) -> OrderedNamedObjectList['Command']:
        pass

    @property
    @abstractmethod
    def data(self) -> DataViewer:
        pass

    @property
    @abstractmethod
    def metadata(self) -> MetadataViewer:
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        pass

    @property
    @abstractmethod
    def data_url(self) -> str:
        pass

    @property
    @abstractmethod
    def metadata_url(self) -> str:
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass


TE = TypeVar('TE', bound=DataEditor)


class Context(Generic[TE], metaclass=ABCMeta):
    """
    The context is passed to the action implementation.

    It is used by the action implementation to change the
    artifact data and to update the metrics.
    """

    @property
    @abstractmethod
    def data(self) -> TE:
        pass

    @property
    @abstractmethod
    def metrics(self) -> NamedObjectMap[MetricEditor]:
        pass

    @property
    @abstractmethod
    def interrupt_requested(self) -> bool:
        pass


class Command(OrderedNamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def artifact(self) -> Artifact:
        pass

    @property
    @abstractmethod
    def action_name(self) -> str:
        pass

    @property
    @abstractmethod
    def arguments(self) -> NamedObjectMap[Argument]:
        pass

    @property
    @abstractmethod
    def metrics(self) -> NamedObjectMap[MetricViewer]:
        pass

    @abstractmethod
    def open_log(self) -> IO[str]:
        pass

    @property
    @abstractmethod
    def interrupt_requested(self) -> bool:
        pass


def get_tool_from_url(url: str) -> Tool:

    if url.startswith('http://'):

        # late import to avoid loops
        http_tool = importlib.import_module('..impl.tool.http_tool_client', package=__package__)

        return http_tool.HttpTool(url)

    else:
        raise Exception("Unsupported tool url " + url)
