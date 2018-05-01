from abc import ABCMeta, abstractmethod

from .format import Viewer, Editor, Server, Format, FormatList


class DataViewer(Viewer, metaclass=ABCMeta):
    """
    DataViewer is the actual information contained in the artifact.
    """


class DataEditor(Editor, metaclass=ABCMeta):
    """
    DataEditor is a class used to edit the data of an artifact
    """


class DataServer(Server, metaclass=ABCMeta):
    """
    Published the artifact data as HTTP
    """
    pass


class DataFormat(Format[DataViewer, DataEditor, DataServer], metaclass=ABCMeta):

    @property
    @abstractmethod
    def metadata_type(self) -> str:
        pass


data_formats = FormatList[DataFormat]()   # type: FormatList[DataFormat]
