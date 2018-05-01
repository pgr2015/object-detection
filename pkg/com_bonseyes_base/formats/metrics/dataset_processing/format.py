from urllib.parse import urlparse

from .api import DATA_PROCESSING_METRIC_FORMAT_NAME
from ....lib.api.metrics import MetricFormat, MetricServer
from .api import DatasetProcessingMetricViewer, \
    DatasetProcessingMetricEditor
from .client import HttpDatasetProcessingMetricViewer
from .server import DatasetProcessingMetricServer
from .storage import StoredDatasetProcessingMetricViewer, \
    StoredDatasetProcessingMetricEditor
from ....lib.impl.storage.file_storage import FileStoredBlob


class DatasetProcessingMetricFormat(MetricFormat):

    @property
    def type_name(self) -> str:
        return DATA_PROCESSING_METRIC_FORMAT_NAME

    def get_viewer(self, url: str, name: str) -> DatasetProcessingMetricViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredDatasetProcessingMetricViewer(FileStoredBlob(path), name)

        elif scheme == 'http':
            return HttpDatasetProcessingMetricViewer(url, name)

        else:
            raise Exception("Unsupported url:" + url)

    def get_editor(self, url: str, name: str) -> DatasetProcessingMetricEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredDatasetProcessingMetricEditor(FileStoredBlob(path), name)

        else:
            raise Exception("Unsupported url:" + url)

    def get_server(self) -> MetricServer:
        return DatasetProcessingMetricServer()
