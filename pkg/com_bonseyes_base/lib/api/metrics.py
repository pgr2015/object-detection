from abc import ABCMeta

from .format import Viewer, Editor, Server, Format, FormatList
from .utils import NamedObject


class MetricViewer(Viewer, NamedObject, metaclass=ABCMeta):
    pass


class MetricEditor(Editor, NamedObject, metaclass=ABCMeta):
    pass


class MetricServer(Server[MetricViewer], metaclass=ABCMeta):
    pass


class MetricFormat(Format[MetricViewer, MetricEditor, MetricServer], metaclass=ABCMeta):

    def get_viewer(self, name: str, url: str) -> MetricViewer:
        raise Exception("No viewer available")

    def get_editor(self, name: str, url: str) -> MetricEditor:
        raise Exception("No editor available")

    def get_server(self) -> MetricServer:
        raise Exception("No server available")


metric_formats = FormatList[MetricFormat]()
