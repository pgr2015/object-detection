from typing import Optional

from ....lib.impl.formats.http import HttpMetricViewer
from .api import DatasetProcessingMetricViewer
from ....lib.impl.rpc.http_rpc_client import get_json


class HttpDatasetProcessingMetricViewer(DatasetProcessingMetricViewer, HttpMetricViewer):

    @property
    def processed_samples(self) -> int:
        return get_json(self._url)['processed_samples']

    @property
    def remaining_samples(self) -> Optional[int]:
        return get_json(self._url).get('remaining_samples')
