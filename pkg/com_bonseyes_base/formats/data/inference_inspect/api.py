from abc import abstractmethod, ABCMeta

from ....lib.api.data import DataViewer, DataEditor
from ..database.api import Dataset


INFERENCE_INSPECT_DATA_FORMAT_NAME = 'com.bonseyes.data.inference-inspect.0.1'

class LayerData:
    @property
    @abstractmethod
    def layer_name(self) -> str:
        pass

    @property
    @abstractmethod
    def layer_type(self) -> int:
        pass

    @property
    @abstractmethod
    def layout(self) -> int:
        pass

    @property
    @abstractmethod
    def data_type(self) -> int:
        pass

    @property
    @abstractmethod
    def frac_bits(self) -> int:
        pass

    @property
    @abstractmethod
    def output(self) -> Dataset:
        pass


class InferenceInspectViewer(DataViewer, metaclass=ABCMeta):
    # @property
    # @abstractmethod
    # def network_name(self) -> str:
    #     pass
    #
    # @property
    # @abstractmethod
    # def layer_names(self) -> List[str]:
    #     pass
    #
    # @property
    # @abstractmethod
    # def data(self, layer_name: str) -> LayerData:
    #     pass
    pass

class InferenceInspectEditor(DataEditor, metaclass=ABCMeta):
    pass