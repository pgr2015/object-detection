from typing import IO

from ....lib.api.storage import StoredBlob, Editor
from .api import BlobMetricViewer, BlobMetricEditor


class StoredBlobMetricViewer(BlobMetricViewer):

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


class StoredBlobMetricEditor(BlobMetricEditor):

    def __init__(self, stored_blob: StoredBlob, name: str):
        self._stored_blob = stored_blob
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def stored_blob(self) -> StoredBlob:
        return self._stored_blob

    def edit_content(self) -> Editor:
        return self.stored_blob.edit()
