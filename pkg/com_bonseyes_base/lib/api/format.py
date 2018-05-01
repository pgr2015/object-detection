import logging
from abc import ABCMeta, abstractmethod
from typing import Dict, Callable, Union, IO
from typing import Generic, TypeVar

from . import storage as storage_api


class Viewer(metaclass=ABCMeta):

    def open(self):
        pass

    def close(self):
        pass

    def view_content(self) -> storage_api.Editor:
        raise NotImplemented()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @abstractmethod
    def as_stream(self) -> IO[bytes]:
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        """
        URL of the backend storage for this object
        :return:
        """
        pass


class Editor(metaclass=ABCMeta):

    @abstractmethod
    def edit_content(self) -> storage_api.Editor:
        """
        Provide access to the on-disk representation of the object
        """
        pass

    def start(self):
        """ Start editing the object"""
        pass

    def commit(self):
        """ Commit the changed to the object"""
        pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit()


TV_co = TypeVar('TV_co', bound=Viewer, covariant=True)


class Server(Generic[TV_co], metaclass=ABCMeta):

    @abstractmethod
    def get(self, data: TV_co, path: str):
        pass


TE_co = TypeVar('TE_co', bound=Editor, covariant=True)
TS_co = TypeVar('TS_co', bound=Server[TV_co], covariant=True)


class Format(Generic[TV_co, TE_co, TS_co], metaclass=ABCMeta):

    @property
    @abstractmethod
    def type_name(self) -> str:
        pass

    def get_viewer(self, url: str) -> TV_co:
        raise Exception("No viewer available")

    def get_editor(self, url: str) -> TE_co:
        raise Exception("No editor available")

    def get_server(self) -> TS_co:
        raise Exception("No server available")


TF_co = TypeVar('TF_co', bound=Format, covariant=True)


class FormatList(Generic[TF_co]):

    def __init__(self):
        self._formats = {}   # type: Dict[str, TF_co]

    def register(self, format_obj: Union[TF_co, Callable[[], TF_co]], type_name: str=None) -> None:

        if isinstance(format_obj, Format):
            logging.info("Registering format " + format_obj.type_name)
            self._formats[format_obj.type_name] = lambda: format_obj
        else:
            logging.info("Registering format " + type_name)
            self._formats[type_name] = format_obj

    def get(self, type_name: str) -> TF_co:
        return self._formats[type_name]()
