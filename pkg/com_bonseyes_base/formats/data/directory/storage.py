from typing import IO

from ....lib.api.storage import Storage, Editor
from .api import DirectoryDataViewer, DirectoryDataEditor
from ....lib.impl.utils import TarBuilder, TarBuilderReader


class StoredDirectoryDataViewer(DirectoryDataViewer):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    def as_stream(self) -> IO[bytes]:
        tar_builder = TarBuilder(self._storage)
        return TarBuilderReader(tar_builder)

    def open_blob(self, subpath: str='/', mode: str='r') -> IO:

        if 'w' in mode:
            raise Exception("Cannot open in write mode")

        if not self._storage.exists(subpath):
            raise Exception("File doesn't exist")

        if self._storage.isdir(subpath):

            tar_builder = TarBuilder(self._storage.get_substorage(subpath))
            fp = TarBuilderReader(tar_builder)

            return fp

        else:
            return self._storage.open(subpath, mode)

    def view(self, subpath: str = '/') -> Editor:
        return self._storage.edit(subpath)

    @property
    def url(self) -> str:
        return self._storage.url


class StoredDirectoryDataEditor(DirectoryDataEditor):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    def start(self):
        super().start()
        self._storage.makedirs('/', exist_ok=True)

    @property
    def storage(self) -> Storage:
        return self._storage

    def edit_content(self) -> Editor:
        self._storage.makedirs('/', exist_ok=True)
        return self._storage.edit('/')
