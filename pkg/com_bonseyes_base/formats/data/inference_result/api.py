from abc import abstractmethod, ABCMeta

from ....lib.api.data import DataViewer, DataEditor
from ..database.api import Dataset

INFERENCE_RESULT_DATA_FORMAT_NAME = 'com.bonseyes.data.inference-result.0.1'


class InferenceResultViewer(DataViewer, metaclass=ABCMeta):

    @property
    @abstractmethod
    def values(self) -> Dataset:
        pass


class InferenceResultEditor(DataEditor, metaclass=ABCMeta):
    pass
