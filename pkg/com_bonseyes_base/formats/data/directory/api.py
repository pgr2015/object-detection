from typing import IO

from abc import abstractmethod, ABCMeta

from ....lib.api.data import DataViewer, DataEditor
from ....lib.api.storage import Editor

DIRECTORY_DATA_FORMAT_NAME = 'com.bonseyes.data.directory.0.1'


class DirectoryDataViewer(DataViewer, metaclass=ABCMeta):

    @abstractmethod
    def open_blob(self, subpath: str='/', mode: str='r') -> IO:
        pass

    @abstractmethod
    def view(self, subpath: str='/') -> Editor:
        pass


class DirectoryDataEditor(DataEditor, metaclass=ABCMeta):
    pass
