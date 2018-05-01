from typing import List, IO

from ....lib.api.storage import Editor, StoredBlob
from .api import TimeSeriesMetricViewer, Sample, TimeSeriesMetricEditor


class StoredTimeSeriesMetricViewer(TimeSeriesMetricViewer):

    def __init__(self, stored_blob: StoredBlob, name: str):
        self._stored_blob = stored_blob
        self._name = name

    def as_stream(self) -> IO[bytes]:
        return self._stored_blob.open('rb')

    @property
    def name(self) -> str:
        return self._name

    def samples(self) -> List[Sample]:
        with self._stored_blob.open('r') as fp:

            for idx, line in enumerate(fp.readlines()):
                time_str, value_str = line.split(',')
                yield Sample(float(time_str), idx, float(value_str))

    @property
    def url(self) -> str:
        return self._stored_blob.url


class StoredTimeSeriesMetricEditor(TimeSeriesMetricEditor):

    def __init__(self, stored_blob: StoredBlob, name: str):
        self._stored_blob = stored_blob
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def add_sample(self, time: float, value: float):
        with self._stored_blob.open('w') as fp:

            if fp.tell() != 0:
                fp.write('\n')

            fp.write('%f,%f' % (time, value))

    def edit_content(self) -> Editor:
        return self._stored_blob.edit()
