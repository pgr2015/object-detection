from abc import ABCMeta
from typing import IO, TypeVar, Generic

from ...api.data import DataViewer, DataServer
from ...api.format import Viewer
from ...api.metadata import MetadataViewer, MetadataServer
from ...api.metrics import MetricViewer, MetricServer
from ..rpc.http_rpc_client import get_stream


class HttpViewer(Viewer):
    def __init__(self, url: str):
        self._url = url.rstrip('/') + '/'

    @property
    def url(self):
        return self._url

    def as_stream(self) -> IO[bytes]:
        return get_stream(self._url)


class HttpDataViewer(DataViewer, HttpViewer):
    pass


class HttpMetadataViewer(MetadataViewer, HttpViewer):
    pass


class HttpMetricViewer(MetricViewer, HttpViewer):
    def __init__(self, url: str, name: str):
        HttpViewer.__init__(self, url)
        self._name = name

    @property
    def name(self) -> str:
        return self._name


T = TypeVar('T', bound=DataViewer)


class DataServerBase(Generic[T], DataServer, metaclass=ABCMeta):

    def _get_subpath(self, data: T, path: str):
        raise Exception("Path not supported")

    def get(self, data: T, path: str):
        if path == '/':
            return data.as_stream()
        else:
            return self._get_subpath(data, path)


TM = TypeVar('TM', bound=MetadataViewer)


class MetadataServerBase(Generic[TM], MetadataServer, metaclass=ABCMeta):

    def _get_subpath(self, data: TM, path: str):
        raise Exception("Path not supported")

    def get(self, data: TM, path: str):
        if path == '/':
            return data.as_stream()
        else:
            return self._get_subpath(data, path)


TMT = TypeVar('TMT', bound=MetadataViewer)


class MetricServerBase(Generic[TMT], MetricServer, metaclass=ABCMeta):

    def _get_subpath(self, data: TMT, path: str):
        raise Exception("Path not supported")

    def get(self, data: TMT, path: str):
        if path == '/':
            return data.as_stream()
        else:
            return self._get_subpath(data, path)
