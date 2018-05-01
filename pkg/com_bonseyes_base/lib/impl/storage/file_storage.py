import os
from fcntl import flock, LOCK_SH, LOCK_EX
from typing import AnyStr, IO, List, Iterator

import shutil
from typing import Optional
from typing import TextIO
from uuid import uuid4

from ...api.context import Context, ContextEntry
from ...api.storage import Storage, Editor, StorageEntry, StoredBlob


class PathEditor(Editor):

    def __init__(self, path: str) -> None:
        self._path = path

    def open(self) -> str:
        return self._path

    def close(self) -> None:
        pass


class FileStorageEntry(StorageEntry):

    def __init__(self, path: str, name: str):
        self._path = path
        self._name = name.lstrip('/')

    @property
    def name(self) -> str:
        return self._name

    def open(self, mode: str) -> IO:
        return open(os.path.join(self._path, self._name), mode)


class FileStorage(Storage):

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir

    def _get_full_path(self, path: str) -> str:
        # FIXME: security: check that path is a child of data_dir

        if path.startswith('/'):
            path = path[1:]

        return os.path.join(self.data_dir, path.lstrip('/'))

    @property
    def name(self) -> str:
        return os.path.basename(self.data_dir)

    @property
    def url(self) -> str:
        return 'file://' + self.data_dir

    def open(self, path: str, mode: str) -> IO[AnyStr]:
        full_path = self._get_full_path(path)
        dir_name = os.path.dirname(full_path)

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        return open(full_path, mode)

    def exists(self, path: str) -> bool:
        return os.path.exists(self._get_full_path(path))

    def create_new_substorage(self) -> 'Storage':

        while True:

            path = str(uuid4())

            try:
                self.makedirs(path, exist_ok=False)
                break
            except OSError:
                pass

        substorage_path = self._get_full_path(path)

        return FileStorage(substorage_path)

    def makedirs(self, path: str, exist_ok: bool=False) -> None:
        os.makedirs(self._get_full_path(path), exist_ok=exist_ok)

    def delete(self, path: str) -> None:
        full_path = self._get_full_path(path)

        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.unlink(full_path)

    def list(self, path: str) -> List[str]:
        return os.listdir(self._get_full_path(path))

    def isdir(self, path: str) -> bool:
        return os.path.isdir(self._get_full_path(path))

    def edit(self, path: str) -> Editor:
        return PathEditor(self._get_full_path(path))

    def get_stored_blob(self, path: str) -> 'StoredBlob':
        blob_path = self._get_full_path(path)
        return FileStoredBlob(blob_path)

    def get_substorage(self, path: str) -> 'Storage':

        substorage_path = self._get_full_path(path)

        if not os.path.exists(substorage_path):
            os.makedirs(substorage_path)

        return FileStorage(substorage_path)

    def move(self, src_path: str, dst_path: str) -> None:
        os.rename(self._get_full_path(src_path), self._get_full_path(dst_path))

    def copy(self, src_path: str, dst_path: str) -> None:
        shutil.copytree(self._get_full_path(src_path), self._get_full_path(dst_path))

    @property
    def entries(self) -> List[StorageEntry]:
        for root, dirs, files in os.walk(self.data_dir):
            for file_name in files:

                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, self.data_dir)

                yield FileStorageEntry(self.data_dir, rel_path)


class FileStoredBlob(StoredBlob):

    def __init__(self, path: str) -> None:
        self._path = path

    @property
    def url(self) -> str:
        return 'file://' + self._path

    def open(self, mode: str) -> IO:
        return open(self._path, mode)

    @property
    def exists(self) -> bool:
        return os.path.exists(self._path)

    def edit(self) -> Editor:
        return PathEditor(self._path)


class FileContextEntry(ContextEntry):

    def __init__(self, path: str, name: str):
        self._path = path
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def open(self) -> IO[bytes]:
        return open(os.path.join(self._path, self._name), 'rb')


class FileContext(Context):

    def __init__(self, path: str):
        self._path = path

    def get_entry(self, name: str) -> ContextEntry:
        return FileContextEntry(self._path, name)

    def entries(self) -> List[ContextEntry]:
        for root, dirs, files in os.walk(self._path):
            for file_name in files:

                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, self._path)

                yield FileContextEntry(self._path, rel_path)

    def __iter__(self) -> Iterator[ContextEntry]:
        return self.entries()


class SimpleLock:

    def __init__(self, file_name: str, shared: bool=False) -> None:
        self._file_name = file_name
        self._shared = shared
        self._fd = None  # type: Optional[TextIO]

    def lock(self) -> None:

        if self._fd is not None:
            return

        self._fd = open(self._file_name)

        if self._shared:
            flock(self._fd, LOCK_SH)
        else:
            flock(self._fd, LOCK_EX)

    def unlock(self) -> None:
        if self._fd is None:
            return

        self._fd.close()
        self._fd = None

    def __enter__(self) -> 'SimpleLock':
        self.lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self.unlock()
