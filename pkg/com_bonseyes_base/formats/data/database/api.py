from typing import Optional, Tuple, Any

from abc import abstractmethod, ABCMeta

import h5py
import numpy

from ....lib.api.data import DataViewer, DataEditor
from ....lib.api.utils import OrderedNamedObjectList, OrderedNamedObject, NamedObjectMap, NamedObject


DATABASE_DATA_FORMAT_NAME = 'com.bonseyes.data.database.0.1'


class DataType:
    FLOAT32 = 'float32'
    UINT32 = 'uint32'
    STRING = 'string'

    @staticmethod
    def to_numpy_dtype(type_name: str):
        if type_name == DataType.FLOAT32:
            return numpy.float32
        elif type_name == DataType.UINT32:
            return numpy.uint32
        elif type_name == DataType.STRING:
            return h5py.special_dtype(vlen=numpy.unicode)
        else:
            raise Exception("Unsupported type " + type_name)

    @staticmethod
    def from_numpy_dtype(dtype: numpy.dtype):

        dt = h5py.special_dtype(vlen=numpy.unicode)

        if dtype == "float32":
            return DataType.FLOAT32
        elif dtype == "uint32":
            return DataType.UINT32
        elif dtype == dt and dtype.metadata == dt.metadata:
            return DataType.STRING
        else:
            raise Exception("Unsupported type " + str(dtype))


class Dimension(OrderedNamedObject, metaclass=ABCMeta):

    def __init__(self, name: str, index: int, size: int):
        self._name = name
        self._index = index
        self._size = size

    @property
    def name(self) -> str:
        return self._name

    @property
    def index(self) -> int:
        return self._index

    @property
    def size(self) -> int:
        return self._size


class Attribute(NamedObject):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def value(self) -> Any:
        pass

    @property
    @abstractmethod
    def data_type(self) -> str:
        pass


class Dataset(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def __getitem__(self, item) -> numpy.ndarray:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> OrderedNamedObjectList[Dimension]:
        pass

    @property
    @abstractmethod
    def data_type(self) -> str:
        pass

    @property
    @abstractmethod
    def attributes(self) -> NamedObjectMap[Attribute]:
        pass



class EditableDataset(Dataset, metaclass=ABCMeta):

    @abstractmethod
    def __setitem__(self, item, value) -> None:
        pass

    @abstractmethod
    def resize(self, size: int, axis: int) -> None:
        pass

    @abstractmethod
    def set_attribute(self, name: str, value: Any, dtype: str):
        pass


class DatabaseViewer(DataViewer, metaclass=ABCMeta):

    @property
    @abstractmethod
    def datasets(self) -> NamedObjectMap[Dataset]:
        pass


class DatabaseEditor(DataEditor, metaclass=ABCMeta):

    @abstractmethod
    def add_dataset(self, name: str,
                    dimension_names: Optional[Tuple[str]],
                    shape: Tuple[int],
                    maxshape: Optional[Tuple[Optional[int]]],
                    data_type: str) -> EditableDataset:
        pass

    @property
    @abstractmethod
    def datasets(self) -> NamedObjectMap[EditableDataset]:
        pass
