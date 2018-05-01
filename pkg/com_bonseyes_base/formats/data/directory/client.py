from typing import IO, Optional

from ....lib.api.storage import Editor
from ....lib.impl.formats.http import HttpDataViewer
from .api import DirectoryDataViewer
from ....lib.impl.rpc.http_rpc_client import get_stream


class HttpDirectoryDataViewer(DirectoryDataViewer, HttpDataViewer):

    def open_blob(self,  subpath: Optional[str]='/', mode: str='r') -> IO:
        return get_stream(self._url + subpath)

    def view(self, subpath: str = '/') -> Editor:
        raise NotImplemented()
