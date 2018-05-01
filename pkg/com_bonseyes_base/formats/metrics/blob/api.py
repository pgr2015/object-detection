from abc import ABCMeta

from ....lib.api.metrics import MetricViewer, MetricEditor

BLOB_METRIC_FORMAT_NAME = 'com.bonseyes.metrics.blob.1.0'


class BlobMetricViewer(MetricViewer, metaclass=ABCMeta):
    pass


class BlobMetricEditor(MetricEditor, metaclass=ABCMeta):
    pass
