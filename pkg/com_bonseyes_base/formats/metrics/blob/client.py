from ....lib.impl.formats.http import HttpMetricViewer
from .api import BlobMetricViewer


class HttpBlobMetricViewer(BlobMetricViewer, HttpMetricViewer):
    pass
