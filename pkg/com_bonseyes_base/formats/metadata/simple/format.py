from urllib.parse import urlparse

from ...metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from ....lib.api.metadata import MetadataFormat
from .api import SimpleMetadataViewer, SimpleMetadataEditor
from .client import HttpSimpleMetadataViewer
from .server import SimpleMetadataServer
from .storage import StoredSimpleMetadata, StoredSimpleMetadataEditor
from ....lib.impl.storage.file_storage import FileStoredBlob


class SimpleMetadataFormat(MetadataFormat):

    @property
    def type_name(self) -> str:
        return SIMPLE_METADATA_FORMAT_NAME

    def get_viewer(self, url: str) -> SimpleMetadataViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredSimpleMetadata(FileStoredBlob(path))

        elif scheme == 'http':
            return HttpSimpleMetadataViewer(url)

        else:
            raise Exception("Unsupported url:" + url)

    def get_editor(self, url: str) -> SimpleMetadataEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredSimpleMetadataEditor(FileStoredBlob(path))
        else:
            raise Exception("Unsupported url:" + url)

    def get_register_server(self):
        return SimpleMetadataServer()
