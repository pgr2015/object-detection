from abc import abstractmethod, ABCMeta
from typing import TypeVar, Generic, Dict, List, Callable, Union, Any


class NamedObject(metaclass=ABCMeta):

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class OrderedNamedObject(metaclass=ABCMeta):

    @property
    @abstractmethod
    def name(self) -> Union[str, None]:
        pass

    @property
    @abstractmethod
    def index(self) -> int:
        pass


T_co = TypeVar('T_co', bound=NamedObject, covariant=True)
TO_co = TypeVar('TO_co', bound=OrderedNamedObject, covariant=True)


class NamedObjectMap(Generic[T_co], metaclass=ABCMeta):

    @property
    @abstractmethod
    def all(self) -> List[T_co]:
        pass

    @property
    @abstractmethod
    def names(self) -> List[str]:
        pass

    @abstractmethod
    def get(self, name: str) -> T_co:
        pass

    @property
    @abstractmethod
    def count(self) -> int:
        pass


class OrderedNamedObjectList(Generic[TO_co], metaclass=ABCMeta):

    @property
    @abstractmethod
    def all(self) -> List[TO_co]:
        pass

    @property
    @abstractmethod
    def names(self) -> List[str]:
        pass

    @abstractmethod
    def get_by_index(self, index: int) -> TO_co:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> TO_co:
        pass

    @property
    @abstractmethod
    def count(self) -> int:
        pass


class MemoryNamedObjectMap(Generic[T_co], NamedObjectMap[T_co]):

    def __init__(self, data: Dict[str, T_co]) -> None:
        self._dict = data

    @property
    def all(self) -> List[T_co]:
        return list(self._dict.values())

    @property
    def names(self) -> List[str]:
        return list(self._dict.keys())

    def get(self, name: str) -> T_co:
        return self._dict[name]

    @property
    def count(self) -> int:
        return len(self._dict)


class MemoryOrderedObjectList(Generic[TO_co], OrderedNamedObjectList[TO_co]):

    def __init__(self, data: List[TO_co]) -> None:
        self._data = data
        self._data_by_name = {item.name: item for item in data if item.name is not None}

    @property
    def all(self) -> List[TO_co]:
        return list(self._data)

    @property
    def names(self) -> List[str]:
        return list(self._data_by_name.keys())

    def get_by_index(self, index: int) -> TO_co:
        return self._data[index]

    def get_by_name(self, name: str) -> TO_co:
        return self._data_by_name[name]

    @property
    def count(self) -> int:
        return len(self._data)


class NamedDataView(NamedObject):

    def __init__(self, name: str, data: Dict) -> None:
        self._name = name
        self._data = data

    @property
    def name(self) -> str:
        return self._name


class OrderedNamedDataView(OrderedNamedObject):

    def __init__(self, index: int, data: Dict) -> None:
        self._index = index
        self._data = data

    @property
    def index(self) -> int:
        return self._index

    @property
    def name(self) -> str:
        return self._data.get('name', None)


VT = TypeVar('VT', bound=NamedObject)


def create_data_views_from_dict(data: Dict[str, Dict], base: Callable[[str, Any], VT]) -> NamedObjectMap[VT]:
    items = {name: base(name, item) for name, item in data.items()}
    return MemoryNamedObjectMap(items)


VTO = TypeVar('VTO', bound=OrderedNamedObject)


def create_data_views_from_list(data: List[Dict], base: Callable[[int, Any], VTO]) -> OrderedNamedObjectList[VTO]:
    items = [base(idx, item) for idx, item in enumerate(data)]
    return MemoryOrderedObjectList(items)
