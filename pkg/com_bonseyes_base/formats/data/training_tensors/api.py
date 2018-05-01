from abc import ABCMeta, abstractmethod

from ....lib.api.data import DataViewer, DataEditor
from ..data_tensors.api import DataTensorsViewer, DataTensorsEditor

TRAINING_GROUP_NAME = 'learning'
VALIDATION_GROUP_NAME = 'validation'

TRAINING_TENSORS_DATA_FORMAT_NAME = 'com.bonseyes.data.training-tensors.0.1'


class TrainingTensorsViewer(DataViewer, metaclass=ABCMeta):

    @property
    @abstractmethod
    def learning_data(self) -> DataTensorsViewer:
        pass

    @property
    @abstractmethod
    def validation_data(self) -> DataTensorsViewer:
        pass


class TrainingTensorsEditor(DataEditor, metaclass=ABCMeta):

    @property
    @abstractmethod
    def learning_data(self) -> DataTensorsEditor:
        pass

    @property
    @abstractmethod
    def validation_data(self) -> DataTensorsEditor:
        pass
