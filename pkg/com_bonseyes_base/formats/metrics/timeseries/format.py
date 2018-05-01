from urllib.parse import urlparse

from com_bonseyes_base.formats.metrics.timeseries.api import TIMESERIES_METRIC_FORMAT_NAME
from ....lib.api.metrics import MetricServer, MetricFormat
from .api import TimeSeriesMetricViewer, TimeSeriesMetricEditor
from .client import HttpTimeSeriesMetricViewer
from .server import TimeSeriesMetricServer
from .storage import StoredTimeSeriesMetricViewer, StoredTimeSeriesMetricEditor
from ....lib.impl.storage.file_storage import FileStoredBlob


class TimeSeriesMetricFormat(MetricFormat):

    @property
    def type_name(self) -> str:
        return TIMESERIES_METRIC_FORMAT_NAME

    def get_viewer(self, url: str, name: str) -> TimeSeriesMetricViewer:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredTimeSeriesMetricViewer(FileStoredBlob(path), name)

        elif scheme == 'http':
            return HttpTimeSeriesMetricViewer(url, name)

        else:
            raise Exception("Unsupported url:" + url)

    def get_editor(self, url: str, name: str) -> TimeSeriesMetricEditor:

        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        if scheme == 'file':
            return StoredTimeSeriesMetricEditor(FileStoredBlob(path), name)

        else:
            raise Exception("Unsupported url:" + url)

    def get_server(self) -> MetricServer:
        return TimeSeriesMetricServer()
