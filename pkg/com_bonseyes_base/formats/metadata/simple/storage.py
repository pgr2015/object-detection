import json
from typing import Dict, IO

from .api import SimpleMetadataEditor
from ....lib.api.metadata import DataViewer, MetricViewer

from ....lib.api.storage import Editor, StoredBlob
from ....lib.api.utils import NamedObjectMap
from .api import SimpleMetadataViewer


class StoredSimpleMetadata(SimpleMetadataViewer):

    def __init__(self, stored_blob: StoredBlob):
        self._stored_blob = stored_blob

    def get(self) -> Dict:
        with self._stored_blob.open('r') as fp:
            return json.load(fp)

    def as_stream(self) -> IO[bytes]:
        return self._stored_blob.open('rb')

    @property
    def url(self) -> str:
        return self._stored_blob.url


class StoredSimpleMetadataEditor(SimpleMetadataEditor):

    def __init__(self, stored_blob: StoredBlob):
        self._stored_blob = stored_blob

    def update(self, data: DataViewer, metrics: NamedObjectMap[MetricViewer]) -> None:
        with self._stored_blob.open('w') as fp:
            json.dump({}, fp)

    def edit_content(self) -> Editor:
        return self._stored_blob.edit()

    def set(self, data: Dict):
        with self._stored_blob.open('w') as fp:
            json.dump(data, fp)
