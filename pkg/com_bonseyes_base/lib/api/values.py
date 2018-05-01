"""
Values classes used to represent arguments to parameters of workflows and artifacts.
"""

from abc import ABCMeta, abstractmethod
from typing import IO, Union, Dict, List, Any, Iterator

from . import storage as storage_api
from .utils import NamedObject


class ValueType:
    """
    String identifiers for value types (used in YAML files)
    """
    PLAIN_OBJECT = 'json'
    RESOURCE = 'resource'
    STRING = 'string'
    ARCHIVE = 'archive'
    URL = 'url'


class Value(metaclass=ABCMeta):
    """
    Abstract class for a value
    """

    @property
    @abstractmethod
    def type(self) -> str:
        """
        Returns the string type of the value

        :return: one of the ValueType constants
        """
        pass

    @abstractmethod
    def get(self) -> Any:
        """
        Returns the actual value

        :return: what is contained in the value
        """
        pass

    def as_resource(self) -> 'ResourceValue':
        raise ValueError("Impossible to cast to resource")

    def as_archive(self) -> 'ArchiveValue':
        raise ValueError("Impossible to cast to archive")

    def as_plain_object(self) -> 'PlainObjectValue':
        raise ValueError("Impossible to cast to plain object")

    def as_string(self) -> 'StringValue':
        raise ValueError("Impossible to cast to str")

    def as_url(self) -> 'UrlValue':
        raise ValueError("Impossible to cast to url")

    def convert_to(self, dest_type: str) -> 'Value':

        if dest_type == ValueType.STRING:
            return self.as_string()

        elif dest_type == ValueType.PLAIN_OBJECT:
            return self.as_plain_object()

        elif dest_type == ValueType.RESOURCE:
            return self.as_resource()

        elif dest_type == ValueType.URL:
            return self.as_url()

        else:
            raise ValueError("Invalid type " + dest_type)


class StringValue(Value):

    @property
    def type(self) -> str:
        return ValueType.STRING

    @abstractmethod
    def get(self) -> str:
        pass

    @abstractmethod
    def copy_from(self, value: 'StringValue') -> None:
        pass

    def as_string(self):
        return self


class UrlValue(Value):

    @property
    def type(self) -> str:
        return ValueType.URL

    @abstractmethod
    def get(self) -> str:
        pass

    @abstractmethod
    def copy_from(self, value: 'UrlValue') -> None:
        pass

    def as_url(self):
        return self


class ResourceValue(Value):

    @property
    def type(self) -> str:
        return ValueType.RESOURCE

    @property
    @abstractmethod
    def url(self) -> Union[str, None]:
        pass

    @abstractmethod
    def get(self) -> bytes:
        pass

    @abstractmethod
    def open(self) -> IO[bytes]:
        pass

    def edit(self) -> 'storage_api.Editor':
        raise NotImplemented("Not implemented")

    def copy_from(self, value: 'ResourceValue') -> None:
        raise NotImplemented("Not implemented")

    def as_resource(self):
        return self


class ArchiveEntry(metaclass=ABCMeta):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def open(self) -> IO[bytes]:
        pass


class ArchiveValue(Value):

    @property
    def type(self) -> str:
        return ValueType.ARCHIVE

    @property
    @abstractmethod
    def url(self) -> Union[str, None]:
        pass

    @abstractmethod
    def get_entry(self, name: str) -> ArchiveEntry:
        pass

    @property
    @abstractmethod
    def entries(self) -> List[ArchiveEntry]:
        pass

    def as_archive(self) -> 'ArchiveValue':
        return self

    @abstractmethod
    def open(self) -> IO[bytes]:
        pass

    def __iter__(self) -> Iterator[ArchiveEntry]:
        return iter(self.entries)

    def get(self) -> 'storage_api.Editor':
        raise NotImplemented("Not implemented")

    def copy_from(self, value: 'ArchiveValue') -> None:
        raise NotImplemented("Not implemented")


PlainObjectType = Union[Dict, List, str, int, float, bool, bytes, None]


class PlainObjectValue(Value):

    @property
    def type(self) -> str:
        return ValueType.PLAIN_OBJECT

    @abstractmethod
    def get(self) -> PlainObjectType:
        pass

    @abstractmethod
    def copy_from(self, value: 'PlainObjectValue') -> None:
        pass

    def as_plain_object(self):
        return self


class Argument(NamedObject):

    @property
    @abstractmethod
    def value(self) -> Value:
        pass
