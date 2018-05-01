from urllib.parse import urlparse


from ....lib.api.metrics import MetricServer, MetricFormat
from .api import BlobMetricViewer, BlobMetricEditor
from .client import HttpBlobMetricViewer
from .server import BlobMetricServer
from .storage import StoredBlobMetricViewer, StoredBlobMetricEditor
from ....lib.impl.storage.file_storage import FileStoredBlob


class BlobMetricFormat(MetricFormat):

    @property
    def type_name(self) -> str:
        return 'com.bonseyes.metrics.blob'

    def get_viewer(self, url: str, name: str) -> BlobMetricViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredBlobMetricViewer(FileStoredBlob(path), name)

        elif scheme == 'http':
            return HttpBlobMetricViewer(url, name)

        else:
            raise Exception("Unsupported url:" + url)

    def get_editor(self, url: str, name: str) -> BlobMetricEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredBlobMetricEditor(FileStoredBlob(path), name)

        else:
            raise Exception("Unsupported url:" + url)

    def get_server(self) -> MetricServer:
        return BlobMetricServer()
