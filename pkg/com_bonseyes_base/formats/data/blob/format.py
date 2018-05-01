from urllib.parse import urlparse

from com_bonseyes_base.formats.data.blob.api import BLOB_DATA_FORMAT_NAME
from com_bonseyes_base.formats.metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from ....lib.api.data import DataFormat
from ....lib.impl.storage.file_storage import FileStoredBlob
from ..blob.api import BlobDataViewer, BlobDataEditor
from ..blob.client import HttpBlobDataViewer
from ..blob.server import BlobDataServer
from ..blob.storage import StoredBlobDataViewer, StoredBlobDataEditor


class BlobDataFormat(DataFormat):

    @property
    def type_name(self) -> str:
        return BLOB_DATA_FORMAT_NAME

    def get_viewer(self, url: str) -> BlobDataViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredBlobDataViewer(FileStoredBlob(path))

        elif scheme == 'http':
            return HttpBlobDataViewer(url)

        else:
            raise Exception("Unsupported backend url:" + url)

    def get_editor(self, url: str) -> BlobDataEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredBlobDataEditor(FileStoredBlob(path))
        else:
            raise Exception("Unsupported backend url:" + url)

    def get_server(self):
        return BlobDataServer()

    @property
    def metadata_type(self) -> str:
        return SIMPLE_METADATA_FORMAT_NAME
