from typing import Dict
from urllib.parse import urlparse

from ....lib.api.data import DataFormat
from ....lib.impl.storage.file_storage import FileStorage
from .api import CompositeViewer, CompositeEditor
from .client import HttpCompositeViewer
from .server import CompositeServer
from .storage import StoredCompositeViewer, StoredCompositeEditor


class CompositeFormat(DataFormat):

    def __init__(self, type_name: str, metadata_type: str, components: Dict[str, str]):
        self._components = components
        self._type_name = type_name
        self._metadata_type = metadata_type

    @property
    def type_name(self) -> str:
        return self._type_name

    @property
    def metadata_type(self) -> str:
        return self._metadata_type

    def get_viewer(self, url: str) -> CompositeViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredCompositeViewer(self._components, FileStorage(path))

        elif scheme == 'http':
            return HttpCompositeViewer(url, self._components)

        else:
            raise Exception("Unsupported url:" + url)

    def get_editor(self, url: str) -> CompositeEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredCompositeEditor(self._components, FileStorage(path))
        else:
            raise Exception("Unsupported url:" + url)

    def get_server(self):
        return CompositeServer(self._components)
