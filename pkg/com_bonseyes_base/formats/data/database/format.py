from urllib.parse import urlparse

from com_bonseyes_base.formats.metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from ....lib.api.data import DataFormat
from ....lib.impl.storage.file_storage import FileStoredBlob
from ..database.api import DatabaseViewer, DatabaseEditor, DATABASE_DATA_FORMAT_NAME


class DatabaseFormat(DataFormat):

    @property
    def type_name(self) -> str:
        return DATABASE_DATA_FORMAT_NAME

    @property
    def metadata_type(self) -> str:
        return SIMPLE_METADATA_FORMAT_NAME

    def get_viewer(self, url: str) -> DatabaseViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            from ..database.storage import StoredDatabaseViewer
            return StoredDatabaseViewer(FileStoredBlob(path))

        elif scheme == 'http':
            from ..database.client import HttpDatabaseViewer
            return HttpDatabaseViewer(url)

        else:
            raise Exception("Unsupported backend url:" + url)

    def get_editor(self, url: str) -> DatabaseEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            from ..database.storage import StoredDatabaseEditor
            return StoredDatabaseEditor(FileStoredBlob(path))
        else:
            raise Exception("Unsupported backend url:" + url)

    def get_server(self):
        from ..database.server import DatabaseServer
        return DatabaseServer()
