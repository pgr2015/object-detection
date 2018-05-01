import json
from typing import List, IO, TypeVar, Callable, Generic, Union, Dict, Optional

from abc import ABCMeta, abstractmethod

from .utils import NamedObject, NamedObjectMap, OrderedNamedObject, OrderedNamedObjectList


class Editor(metaclass=ABCMeta):

    @abstractmethod
    def open(self) -> str:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    def __enter__(self) -> 'str':
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:   # type: ignore
        self.close()


class StorageEntry(metaclass=ABCMeta):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def open(self, mode: str) -> IO:
        pass


class Storage(metaclass=ABCMeta):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @abstractmethod
    def open(self, path: str, mode: str) -> IO:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def makedirs(self, path: str, exist_ok: bool=False) -> None:
        pass

    @abstractmethod
    def create_new_substorage(self) -> 'Storage':
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        pass

    @abstractmethod
    def list(self, path: str) -> List[str]:
        pass

    @abstractmethod
    def isdir(self, path: str) -> bool:
        pass

    @abstractmethod
    def edit(self, path: str) -> Editor:
        pass

    @abstractmethod
    def get_substorage(self, path: str) -> 'Storage':
        pass

    @abstractmethod
    def get_stored_blob(self, path: str) -> 'StoredBlob':
        pass

    @abstractmethod
    def move(self, src_path: str, dst_path: str) -> None:
        pass

    @abstractmethod
    def copy(self, src_path: str, dst_path: str) -> None:
        pass

    @property
    @abstractmethod
    def entries(self) -> List[StorageEntry]:
        pass


class StoredBlob(metaclass=ABCMeta):

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @abstractmethod
    def open(self, mode: str) -> IO:
        pass

    @property
    @abstractmethod
    def exists(self) -> bool:
        pass

    @abstractmethod
    def edit(self) -> Editor:
        pass


T = TypeVar('T')


class StoredField(Generic[T], metaclass=ABCMeta):

    def __init__(self, storage: Storage, name: str, required: bool=False):
        self._storage = storage
        self._name = name
        self._required = required
        self._read_mode = 'r'
        self._write_mode = 'w'

    @abstractmethod
    def _read(self, fp: IO) -> T:
        pass

    def get(self, default: T=None) -> Optional[T]:

        if not self._storage.exists(self._name):

            if self._required:
                raise ValueError("Value not present")
            else:
                return default

        with self._storage.open(self._name, self._read_mode) as fp:
            return self._read(fp)

    @abstractmethod
    def _write(self, fp: IO, data: T) -> None:
        pass

    def set(self, data: Optional[T]) -> None:

        if data is None:
            if self._required:
                raise ValueError("Cannot set value to null")
            else:
                if self._storage.exists(self._name):
                    self._storage.delete(self._name)
        else:
            with self._storage.open(self._name, self._write_mode) as fp:
                self._write(fp, data)


class StoredJsonField(StoredField[Dict]):

    def _read(self, fp: IO) -> Dict:
        return json.load(fp)

    def _write(self, fp: IO, data: Dict):
        json.dump(data, fp)


class StorableObject(metaclass=ABCMeta):

    @abstractmethod
    def to_dict(self):
        pass


STO_co = TypeVar('STO_co', bound=StorableObject, covariant=True)


class StoredObjectField(Generic[STO_co], StoredField[STO_co]):

    def __init__(self, storage: Storage, name: str, constructor: Callable[[Dict], STO_co], required: bool=False):
        StoredField.__init__(self, storage, name, required)
        self._constructor = constructor

    def _read(self, fp: IO) -> STO_co:
        return self._constructor(json.load(fp))

    def _write(self, fp: IO, data: STO_co):
        json.dump(data.to_dict(), fp)


class StoredStringField(StoredField[str]):

    def _read(self, fp: IO) -> str:
        return fp.read()

    def _write(self, fp: IO, data: str):
        fp.write(data)


class StoredIntField(StoredField[int]):

    def _read(self, fp: IO) -> int:
        return int(fp.read())

    def _write(self, fp: IO, data: int):
        fp.write(str(data))


class StoredNamedObject(NamedObject):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    @property
    def storage(self) -> Storage:
        return self._storage

    @property
    def name(self) -> str:
        return self._storage.name


TN_co = TypeVar('TN_co', bound=StoredNamedObject, covariant=True)


class StoredOrderedNamedObject(OrderedNamedObject):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._name = StoredStringField(storage, 'name', required=False)

    @property
    def index(self) -> int:
        return int(self._storage.name)

    @property
    def name(self) -> Union[str, None]:
        return self._name.get()


TO_co = TypeVar('TO_co', bound=StoredOrderedNamedObject, covariant=True)


class StoredNamedObjectMap(Generic[TN_co], NamedObjectMap[TN_co]):

    def __init__(self, storage: Storage, base: Callable[..., TN_co]) -> None:
        self._storage = storage
        self._base = base

    @property
    def storage(self):
        return self._storage

    def get(self, key: str) -> TN_co:
        if not self._storage.exists(key):
            raise KeyError("Object %s doesn't exist" % key)

        return self._base(self._storage.get_substorage(key))

    @property
    def names(self) -> List[str]:
        return self._storage.list('/')

    @property
    def count(self) -> int:
        return len(self._storage.list('/'))

    @property
    def all(self) -> List[TN_co]:
        return [self.get(name) for name in self.names]


class StoredOrderedNamedObjectList(Generic[TO_co], OrderedNamedObjectList[TO_co]):

    def __init__(self, storage: Storage, base: Callable[..., TO_co]) -> None:
        self._storage = storage
        self._base = base

    @property
    def storage(self):
        return self._storage

    def get_by_index(self, index: int) -> TO_co:
        if not self._storage.exists(str(index)):
            raise KeyError("Object %d doesn't exist" % index)

        return self._base(self._storage.get_substorage(str(index)))

    def get_by_name(self, name: str) -> TO_co:
        for entry in self.all:
            if entry.name == name:
                return entry

        raise KeyError("Cannot find object with name " + name)

    @property
    def names(self) -> List[str]:
        return [item.name for item in self.all if item.name is not None]

    @property
    def count(self) -> int:
        return len(self._storage.list('/'))

    @property
    def all(self) -> List[TO_co]:
        return [self.get_by_index(idx) for idx in range(0, self.count)]
