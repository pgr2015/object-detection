from abc import ABCMeta, abstractmethod

from ....lib.api.data import DataViewer, DataEditor
from ....lib.api.utils import NamedObjectMap, NamedObject


class ComponentViewer(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def viewer(self) -> DataViewer:
        pass


class CompositeViewer(DataViewer, metaclass=ABCMeta):

    @property
    @abstractmethod
    def components(self) -> NamedObjectMap[ComponentViewer]:
        pass


class ComponentEditor(NamedObject, metaclass=ABCMeta):
    @property
    @abstractmethod
    def editor(self) -> DataEditor:
        pass


class CompositeEditor(DataEditor, metaclass=ABCMeta):

    @property
    @abstractmethod
    def components(self) -> NamedObjectMap[ComponentEditor]:
        pass
