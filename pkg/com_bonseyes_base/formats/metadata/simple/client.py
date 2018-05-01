from typing import Dict

from ....lib.impl.formats.http import HttpMetadataViewer
from .api import SimpleMetadataViewer
from ....lib.impl.rpc.http_rpc_client import get_json


class HttpSimpleMetadataViewer(SimpleMetadataViewer, HttpMetadataViewer):

    def get(self) -> Dict:
        return get_json(self._url)
