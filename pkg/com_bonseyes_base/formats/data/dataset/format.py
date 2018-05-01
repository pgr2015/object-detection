from urllib.parse import urlparse

from .api import DATASET_DATA_FORMAT_NAME
from ...metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from ....lib.api.data import DataFormat

from ....lib.impl.storage.file_storage import FileStorage
from .api import DataSetViewer
from .client import HttpDataSetViewer
from .server import DataSetServer
from .storage import StoredDataSetViewer, StoredDataSetEditor


class DataSetFormat(DataFormat):

    @property
    def type_name(self) -> str:
        return DATASET_DATA_FORMAT_NAME

    def get_viewer(self, url: str) -> DataSetViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredDataSetViewer(FileStorage(path))

        elif scheme == 'http':
            return HttpDataSetViewer(url)

        else:
            raise Exception("Unsupported backend url:" + url)

    def get_editor(self, url: str) -> StoredDataSetEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredDataSetEditor(FileStorage(path))
        else:
            raise Exception("Unsupported backend url:" + url)

    def get_server(self):
        return DataSetServer()

    @property
    def metadata_type(self) -> str:
        return SIMPLE_METADATA_FORMAT_NAME

