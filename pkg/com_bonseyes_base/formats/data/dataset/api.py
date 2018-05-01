from typing import Iterator, List, IO

from abc import abstractmethod, ABCMeta

from ....lib.api.data import DataViewer, DataEditor
from ....lib.api.utils import NamedObject, NamedObjectMap
from ....lib.api.values import Value

DATASET_DATA_FORMAT_NAME = 'com.bonseyes.data.dataset.0.1'


class Datum(NamedObject):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def sample(self) -> 'Sample':
        pass

    @property
    @abstractmethod
    def value(self) -> Value:
        pass


class Sample(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def data(self) -> NamedObjectMap[Datum]:
        pass


class DataSetViewer(DataViewer, metaclass=ABCMeta):

    @property
    @abstractmethod
    def samples(self) -> NamedObjectMap[Sample]:
        pass

    @abstractmethod
    def open_blob(self, name: str) -> IO[bytes]:
        pass

    def stream_data(self, data_types: List[str]) -> Iterator[Datum]:
        for sample in self.samples.all:
            for data_type in data_types:
                try:
                    yield sample.data.get(data_type)
                except KeyError:
                    continue


class EditableSample:

    @abstractmethod
    def add_datum(self, name: str, value: Value):
        pass


class DataSetEditor(DataEditor, metaclass=ABCMeta):

    @abstractmethod
    def add_sample(self, name: str) -> EditableSample:
        pass
