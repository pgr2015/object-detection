from ....lib.impl.formats.http import DataServerBase
from .api import DirectoryDataViewer


class DirectoryDataServer(DataServerBase[DirectoryDataViewer]):

    def _get_subpath(self, data: DirectoryDataViewer, path: str):
        return data.open_blob(path, 'rb')
