from abc import ABCMeta
from typing import Callable, TypeVar, Generic, IO

from ...api.data import DataViewer, DataEditor, DataFormat, DataServer
from ...api.storage import Editor

TV = TypeVar('TV', bound='DataViewer')
TE = TypeVar('TE', bound='DataEditor')


class ExtendedViewer(Generic[TV], DataViewer, metaclass=ABCMeta):

    def __init__(self, parent: TV):
        self._parent = parent

    def open(self):
        self._parent.open()

    def close(self):
        self._parent.close()

    def view_content(self) -> Editor:
        return self._parent.view_content()

    @property
    def url(self):
        return self._parent.url

    def as_stream(self) -> IO[bytes]:
        return self._parent.as_stream()

    @property
    def parent(self) -> TV:
        return self._parent


class ExtendedEditor(Generic[TE], DataEditor, metaclass=ABCMeta):
    def __init__(self, parent: TE):
        self._parent = parent

    def start(self):
        return self._parent.start()

    def commit(self):
        return self._parent.commit()

    @property
    def url(self):
        return self._parent.url

    @property
    def parent(self) -> TE:
        return self._parent

    def edit_content(self) -> Editor:
        return self._parent.edit_content()


EV = TypeVar('EV', bound='ExtendedViewer')
EE = TypeVar('EE', bound='ExtendedEditor')


class ExtendedServer(Generic[EV], DataServer):

    def __init__(self, base_server: DataServer):
        self._base_server = base_server

    def get(self, data: EV, path: str):
        return self._base_server.get(data.parent, path)


class ExtendedFormat(Generic[EV, EE], DataFormat):

    def __init__(self,
                 type_name: str,
                 metadata_type: str,
                 base_format: DataFormat,
                 extended_viewer_factory: Callable[[DataViewer], EV],
                 extended_editor_factory: Callable[[DataEditor], EE]):

        self._type_name = type_name
        self._medatada_type = metadata_type

        self._base_format = base_format
        self._extended_viewer_factory = extended_viewer_factory
        self._extended_editor_factory = extended_editor_factory

    def get_viewer(self, url: str) -> EV:
        base_viewer = self._base_format.get_viewer(url)
        return self._extended_viewer_factory(base_viewer)

    def get_editor(self, url: str) -> EE:
        base_editor = self._base_format.get_editor(url)
        return self._extended_editor_factory(base_editor)

    @property
    def metadata_type(self) -> str:
        return self._medatada_type

    def get_server(self) -> DataServer:
        return ExtendedServer(self._base_format.get_server())

    @property
    def type_name(self) -> str:
        return self._type_name
