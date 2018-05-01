from typing import IO

from ....lib.api.storage import StoredBlob, Editor
from ..blob.api import BlobDataViewer, BlobDataEditor


class StoredBlobDataViewer(BlobDataViewer):

    def __init__(self, storage: StoredBlob):
        self._stored_blob = storage

    def as_stream(self) -> IO[bytes]:
        return self._stored_blob.open('rb')

    @property
    def url(self) -> str:
        return self._stored_blob.url


class StoredBlobDataEditor(BlobDataEditor):

    def __init__(self, storage: StoredBlob):
        self._stored_blob = storage

    @property
    def stored_blob(self) -> StoredBlob:
        return self._stored_blob

    def edit_content(self) -> Editor:
        return self.stored_blob.edit()
