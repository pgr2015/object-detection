import requests
from abc import ABCMeta, abstractmethod
from typing import Any, IO
from urllib.parse import urlparse


class UrlProvider(metaclass=ABCMeta):
    @property
    @abstractmethod
    def schema(self) -> str:
        pass

    def get_url_reader(self, url: str, context: Any) -> 'UrlReader':
        pass


class UrlReader:

    def __init__(self, url: str):
        self._url = url

    @abstractmethod
    def open(self) -> IO[bytes]:
        pass


providers = {}


def get_url_reader(url: str, context: Any) -> UrlReader:

    (scheme, netloc, path, params, query, fragment) = urlparse(url)

    return get_url_provider(scheme).get_url_reader(url, context)


def register_url_provider(provider: UrlProvider):
    providers[provider.schema] = provider


def get_url_provider(schema: str) -> UrlProvider:
    return providers[schema]


class FileUrlReader(UrlReader):

    def open(self) -> IO[bytes]:
        (scheme, netloc, path, params, query, fragment) = urlparse(self._url)
        return open(path, 'rb')


class FileUrlProvider(UrlProvider):

    @property
    def schema(self) -> str:
        return 'file'

    def get_url_reader(self, url: str, context: Any) -> UrlReader:
        return FileUrlReader(url)


register_url_provider(FileUrlProvider())


class HttpUrlReader(UrlReader):
    def open(self):
        ret = requests.get(self._url, stream=True)

        if ret.status_code != 200:
            raise Exception('Error while reading url (code %d) ' % ret.status_code)

        return ret.raw


class HttpUrlProvider(UrlProvider):

    @property
    def schema(self) -> str:
        return 'http'

    def get_url_reader(self, url: str, context: Any) -> UrlReader:
        return HttpUrlReader(url)


register_url_provider(HttpUrlProvider())


class VolumeUrlProvider(UrlProvider):

    @property
    def schema(self) -> str:
        return 'volume'

    def get_url_reader(self, url: str, context: Any) -> UrlReader:
        base_path = '/volumes/'
        (scheme, netloc, path, params, query, fragment) = urlparse(url)
        return FileUrlReader('file://' + base_path + netloc + '/' + path)


register_url_provider(VolumeUrlProvider())
