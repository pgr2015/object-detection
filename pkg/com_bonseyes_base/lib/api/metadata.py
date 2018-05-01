from abc import ABCMeta, abstractmethod

from .data import DataViewer
from .format import Viewer, Editor, Server, Format, FormatList
from .metrics import MetricViewer
from .utils import NamedObjectMap


class MetadataViewer(Viewer, metaclass=ABCMeta):
    """
    MetadataViewer is a light summary of the data that can be used
    to describe the data of the artifact.

    MetadataViewer is typically not processed by tools in a workflow.
    """


class MetadataEditor(Editor, metaclass=ABCMeta):
    @abstractmethod
    def update(self, data: DataViewer, metrics: NamedObjectMap[MetricViewer]):
        """
        Update the metadata from dat and metrics
        """
        pass


class MetadataServer(Server[MetadataViewer], metaclass=ABCMeta):

    @abstractmethod
    def get(self, metadata: MetadataViewer, path: str):
        pass


class MetadataFormat(Format[MetadataViewer, MetadataEditor, MetadataServer], metaclass=ABCMeta):
    pass


metadata_formats = FormatList[MetadataFormat]()
