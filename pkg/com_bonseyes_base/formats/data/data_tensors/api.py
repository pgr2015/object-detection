from typing import List, Tuple

import numpy
from abc import abstractmethod, ABCMeta

from ....lib.api.data import DataViewer, DataEditor
from ..database.api import Dataset

DATA_TENSOR_INPUT_DATASET_NAME = 'input'
DATA_TENSOR_OUTPUT_DATASET_NAME = 'output'
DATA_TENSOR_SAMPLE_NAMES_DATASET_NAME = 'sample_names'
DATA_TENSOR_CLASS_NAMES_DATASET_NAME = 'class_names'

DATA_TENSORS_DATA_FORMAT_NAME = 'com.bonseyes.data.data-tensors.0.1'


class DimensionNames:
    SAMPLE = 'com.bonseyes.sample'
    CHANNEL = 'com.bonseyes.channel'
    HEIGHT = 'com.bonseyes.height'
    WIDTH = 'com.bonseyes.width'
    CLASS_INDEX = 'com.bonseyes.class_index'


class DataTensorsViewer(DataViewer, metaclass=ABCMeta):

    @property
    @abstractmethod
    def input_data(self) -> Dataset:
        pass

    @property
    @abstractmethod
    def output_data(self) -> Dataset:
        pass

    @property
    @abstractmethod
    def class_names(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def sample_names(self) -> List[str]:
        pass


class DataTensorsEditor(DataEditor, metaclass=ABCMeta):

    @abstractmethod
    def initialize(self, class_count: int,
                   input_dimensions: List[Tuple[str, int]],
                   output_dimensions: List[Tuple[str, int]],
                   input_data_type: str,
                   output_data_type: str):
        pass

    @abstractmethod
    def append_sample_data(self, names: List[str],
                           input_data: numpy.ndarray,
                           output_data: numpy.ndarray):
        pass

    @abstractmethod
    def set_class_name(self, class_idx: int, class_name: str) -> None:
        pass
