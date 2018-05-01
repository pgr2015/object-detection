from abc import abstractmethod, ABCMeta
from shutil import copyfileobj
from typing import IO, List, Iterator

from .storage import Storage


class ContextEntry(metaclass=ABCMeta):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def open(self) -> IO[bytes]:
        pass


class Context(metaclass=ABCMeta):

    @abstractmethod
    def get_entry(self, name: str) -> ContextEntry:
        pass

    @abstractmethod
    def entries(self) -> List[ContextEntry]:
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[ContextEntry]:
        pass

    def save_to_storage(self, storage: Storage):
        for entry in self:
            with entry.open() as fpi:
                # FIXME: validate entry.name
                with storage.open(entry.name, 'wb') as fpo:
                    copyfileobj(fpi, fpo)


class MemoryContext(Context):

    def get_entry(self, name: str) -> ContextEntry:
        raise KeyError

    def entries(self) -> List[ContextEntry]:
        return []

    def __iter__(self) -> Iterator[ContextEntry]:
        return iter([])


class StoredContextEntry(ContextEntry):
    def __init__(self, storage: Storage, name: str) -> None:
        self._name = name
        self._storage = storage

    @property
    def name(self) -> str:
        return self._name

    def open(self) -> IO[bytes]:
        return self._storage.open(self._name, 'rb')


class StoredContext(Context):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    @property
    def storage(self):
        return self._storage

    def get_entry(self, name: str) -> ContextEntry:

        if not self._storage.exists(name):
            raise KeyError("Invalid entry name " + name)

        return StoredContextEntry(self._storage, name)

    @property
    def entries(self) -> List[ContextEntry]:
        for entry in self._storage.entries:
            yield StoredContextEntry(self._storage, entry.name)

    def __iter__(self) -> Iterator[ContextEntry]:
        return self.entries
