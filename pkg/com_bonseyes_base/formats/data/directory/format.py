from urllib.parse import urlparse

from com_bonseyes_base.formats.data.directory.api import DIRECTORY_DATA_FORMAT_NAME
from com_bonseyes_base.formats.metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from ....lib.api.data import DataFormat
from ....lib.impl.storage.file_storage import FileStorage
from .api import DirectoryDataViewer, DirectoryDataEditor
from ..directory.client import HttpDirectoryDataViewer
from ..directory.server import DirectoryDataServer
from ..directory.storage import StoredDirectoryDataViewer, StoredDirectoryDataEditor


class DirectoryDataFormat(DataFormat):

    @property
    def type_name(self) -> str:
        return DIRECTORY_DATA_FORMAT_NAME

    def get_viewer(self, url: str) -> DirectoryDataViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredDirectoryDataViewer(FileStorage(path))

        elif scheme == 'http':
            return HttpDirectoryDataViewer(url)

        else:
            raise Exception("Unsupported url:" + url)

    def get_editor(self, url: str) -> DirectoryDataEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredDirectoryDataEditor(FileStorage(path))
        else:
            raise Exception("Unsupported url:" + url)

    def get_server(self):
        return DirectoryDataServer()

    @property
    def metadata_type(self) -> str:
        return SIMPLE_METADATA_FORMAT_NAME
