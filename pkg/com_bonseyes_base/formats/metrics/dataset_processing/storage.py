from typing import Optional, IO

import json

from ....lib.api.storage import Editor, StoredBlob
from .api import DatasetProcessingMetricViewer, \
    DatasetProcessingMetricEditor


class StoredDatasetProcessingMetricViewer(DatasetProcessingMetricViewer):

    def __init__(self, stored_blob: StoredBlob, name: str):
        self._stored_blob = stored_blob
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._stored_blob.url

    def as_stream(self) -> IO[bytes]:
        return self._stored_blob.open('rb')

    @property
    def processed_samples(self) -> int:
        if self._stored_blob.exists:
            with self._stored_blob.open('r') as fp:
                data = json.load(fp)
            return data.get('processed_samples', 0)
        else:
            return 0

    @property
    def remaining_samples(self) -> Optional[int]:
        if self._stored_blob.exists:
            with self._stored_blob.open('r') as fp:
                data = json.load(fp)
            return data.get('remaining_samples', 0)
        else:
            return 0


class StoredDatasetProcessingMetricEditor(DatasetProcessingMetricEditor):

    def __init__(self, stored_blob: StoredBlob, name: str):
        self._stored_blob = stored_blob
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def set_processed_samples(self, processed_samples: int) -> None:
        if self._stored_blob.exists:
            with self._stored_blob.open('r') as fp:
                data = json.load(fp)
        else:
            data = {}

        data['processed_samples'] = processed_samples

        with self._stored_blob.open('w') as fp:
            json.dump(data, fp)

    def set_remaining_samples(self, remaining_samples: int) -> None:
        if self._stored_blob.exists:
            with self._stored_blob.open('r') as fp:
                data = json.load(fp)
        else:
            data = {}

        data['remaining_samples'] = remaining_samples

        with self._stored_blob.open('w') as fp:
            json.dump(data, fp)

    def edit_content(self) -> Editor:
        return self._stored_blob.edit('/')
