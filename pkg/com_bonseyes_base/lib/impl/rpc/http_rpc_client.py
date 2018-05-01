import json
from typing import Dict, Any, IO, TypeVar, Generic, Callable, List

from io import BytesIO
import requests
from requests.models import Response

from ...api.utils import NamedObjectMap, NamedObject, OrderedNamedObjectList, OrderedNamedObject
from ...api.values import Value, PlainObjectValue, StringValue, ResourceValue, UrlValue, ArchiveValue


def prepare_files(params: Dict[str, Any], prefix: str=None) -> Dict[str, Any]:
    """
    Converts a dictionary containing parameters for a POST call to
    a files array suitable to be sent using request.post(..., files=files)

    :param params: the data to convert

    :param prefix: the prefix for the data

    :return: an array ready to be used with requests
    """

    files = {}

    for name, value in params.items():

        if prefix is None:
            full_name = name
        else:
            full_name = prefix + '.' + name

        if isinstance(value, str):
            files[full_name] = (None, value, None)

        elif isinstance(value, dict):
            files.update(prepare_files(value, prefix=full_name))

        elif isinstance(value, Value):

            if isinstance(value, PlainObjectValue):
                data = BytesIO(json.dumps(value.get()).encode('utf-8'))
                mime_type = 'application/vnd.com.bonseyes.data+plainobject'

            elif isinstance(value, StringValue):
                data = BytesIO(value.get().encode('utf-8'))
                mime_type = 'application/vnd.com.bonseyes.data+string'

            elif isinstance(value, ResourceValue):

                if value.url is not None:
                    data = BytesIO(value.url.encode('utf-8'))
                    mime_type = 'application/vnd.com.bonseyes.data+resource.url'
                else:
                    data = value.open()
                    mime_type = 'application/vnd.com.bonseyes.data+resource.blob'

            elif isinstance(value, ArchiveValue):

                if value.url is not None:
                    data = BytesIO(value.url.encode('utf-8'))
                    mime_type = 'application/vnd.com.bonseyes.data+archive.url'
                else:
                    data = value.open()
                    mime_type = 'application/vnd.com.bonseyes.data+archive.blob'

            elif isinstance(value, UrlValue):
                data = BytesIO(value.as_url().get().encode('utf-8'))
                mime_type = 'application/vnd.com.bonseyes.data+url'

            else:
                raise Exception("Cannot send value of type " + value.type + " via HTTP")

            files[full_name] = (full_name, data, mime_type)

    return files


class HttpException(Exception):
    pass


def create_exception_from_request(response: Response):

    message = "Error %d on %s %s" % (response.status_code,
                                     response.request.method,
                                     response.request.url)

    if response.status_code in [500, 400]:
        message += "\n\nError details:"
        message += "\n    " + "\n    ".join(response.text.split('\n'))

    return HttpException(message)


def call_method(url: str, **kwargs) -> Dict:

    files = prepare_files(kwargs)

    with requests.post(url, files=files) as ret:

        if ret.status_code != 200:
            raise create_exception_from_request(ret)

        return ret.json()


def delete(url: str) -> Dict:

    with requests.delete(url) as ret:

        if ret.status_code != 200:
            raise create_exception_from_request(ret)

        return ret.json()


def get_string(url: str) -> str:

    with requests.get(url) as ret:

        if ret.status_code != 200:
            raise create_exception_from_request(ret)

        return ret.text


def get_json(url: str) -> Any:

    with requests.get(url) as ret:

        if ret.status_code != 200:
            raise create_exception_from_request(ret)

        return ret.json()


def get_stream(url: str) -> IO[bytes]:

    ret = requests.get(url, stream=True)

    if ret.status_code != 200:
        raise create_exception_from_request(ret)

    return ret.raw


def follow_stream(url: str) -> IO[bytes]:

    ret = requests.get(url, stream=True, headers={'X-Bonseyes-Follow': 'true'})

    if ret.status_code != 200:
        raise create_exception_from_request(ret)

    return ret.raw


T_co = TypeVar('T_co', bound=NamedObject, covariant=True)


class HttpNamedObjectMap(Generic[T_co], NamedObjectMap[T_co]):

    def __init__(self, url: str, base: Callable[[str, str], T_co]) -> None:
        self._url = url.rstrip('/') + '/'
        self._base = base

    @property
    def url(self):
        return self._url

    def get(self, key: str) -> T_co:
        if key not in self.names:
            raise KeyError("Object %s doesn't exist" % key)

        return self._base(self.url + key + '/', key)

    @property
    def names(self) -> List[str]:
        return get_json(self._url)

    @property
    def count(self) -> int:
        return len(self.names)

    @property
    def all(self) -> List[T_co]:
        return [self.get(name) for name in self.names]


TO_co = TypeVar('TO_co', bound=OrderedNamedObject, covariant=True)


class HttpOrderedNamedObjectList(Generic[TO_co], OrderedNamedObjectList[TO_co]):

    def __init__(self, url: str, base: Callable[[str, int], TO_co]) -> None:
        self._url = url.rstrip('/') + '/'
        self._base = base

    @property
    def url(self):
        return self._url

    def get_by_index(self, index: int) -> TO_co:
        if index < 0 or index > self.count:
            raise KeyError("Object with index %d doesn't exist" % index)

        return self._base(self.url + str(index) + '/', index)

    def get_by_name(self, name: str) -> TO_co:
        raise Exception("Cannot read by name")

    @property
    def names(self) -> List[str]:
        return get_json(self._url)['names']

    @property
    def count(self) -> int:
        return get_json(self._url)['count']

    @property
    def all(self) -> List[TO_co]:
        return [self.get_by_index(name) for name in range(0, self.count)]



