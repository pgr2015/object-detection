from typing import Dict

from ....lib.api.data import DataServer, data_formats
from ....lib.impl.formats.http import DataServerBase
from .api import CompositeViewer


class CompositeServer(DataServerBase[CompositeViewer]):

    def __init__(self, components: Dict[str, str]):

        self._servers = {}   # type: Dict[str, DataServer]

        for part_name, part_type in components.items():
            self._servers[part_name] = data_formats.get(part_type).get_server()

    def _get_subpath(self, data: CompositeViewer, path: str):

        for key, value in self._servers.items():
            if path == key.strip('/') + '/':
                return self._servers[key].get(data.components.get(key).viewer, '/')
            elif path.startswith(key.strip('/') + '/'):
                return self._servers[key].get(data.components.get(key).viewer, path[len(key.strip('/'))+1:].lstrip('/'))
