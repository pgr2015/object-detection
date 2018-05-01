from ....lib.api.storage import Editor
from ....lib.impl.formats.http import HttpDataViewer
from ....lib.impl.storage.http_storage import HttpStoredBlob
from ...data.blob.api import BlobDataViewer


class HttpBlobDataViewer(BlobDataViewer, HttpDataViewer):

    def view_content(self) -> Editor:
        return HttpStoredBlob(self._url).edit()
