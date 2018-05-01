from io import StringIO
from typing import List

from ....lib.impl.formats.http import HttpMetricViewer
from ....lib.impl.rpc.http_rpc_client import get_string
from .api import TimeSeriesMetricViewer, Sample


class HttpTimeSeriesMetricViewer(TimeSeriesMetricViewer, HttpMetricViewer):
    def samples(self) -> List[Sample]:

        data = get_string(self._url)
        fp = StringIO(data)

        for idx, line in enumerate(fp.readlines()):
            time_str, value_str = line.split(',')
            yield Sample(float(time_str), idx, float(value_str))
