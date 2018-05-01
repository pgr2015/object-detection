from ....lib.impl.formats.http import DataServerBase
from .api import DataSetViewer


class DataSetServer(DataServerBase[DataSetViewer]):

    def _get_subpath(self, data: DataSetViewer, path: str):
        return data.open_blob(path)
