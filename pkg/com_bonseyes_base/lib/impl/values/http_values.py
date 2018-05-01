from typing import Union, IO, Any, List

import base64

from ...api.storage import Editor
from ..values.memory_values import PlainObjectValueFromMemory, ResourceValueFromMemory, \
    UrlValueFromMemory, \
    StringValueFromMemory

from ...api.urls import get_url_reader
from ...api.values import StringValue, ValueType, ResourceValue, PlainObjectValue, Value, UrlValue, Argument, \
    ArchiveValue, ArchiveEntry
from ..rpc.http_rpc_client import get_string, get_stream, get_json


class HttpStringValue(StringValue):

    def __init__(self, url: str) -> None:
        self._url = url.rstrip('/') + '/'

    def get(self) -> str:
        return get_string(self._url + 'data')

    def copy_from(self, original: StringValue) -> None:
        raise Exception('Unsupported')

    def as_plain_object(self):
        return PlainObjectValueFromMemory(self.get())

    def as_resource(self):
        return ResourceValueFromMemory(url=self.get())

    def as_url(self):
        return UrlValueFromMemory(self.get())


class HttpUrlValue(UrlValue):

    def __init__(self, url: str) -> None:
        self._url = url.rstrip('/') + '/'

    def get(self) -> str:
        return get_string(self._url + 'data')

    def copy_from(self, original: UrlValue) -> None:
        raise Exception('Unsupported')

    def as_string(self):
        return StringValueFromMemory(self.get())

    def as_plain_object(self):
        return PlainObjectValueFromMemory(self.get())

    def as_resource(self):
        return ResourceValueFromMemory(url=self.get())


class HttpResourceValue(ResourceValue):

    def __init__(self, url: str, context: Any=None) -> None:
        self._url = url.rstrip('/') + '/'
        self._context = context

    @property
    def url(self) -> Union[str, None]:
        if get_string(self._url + 'subtype') == 'url':
            return get_string('data')
        else:
            return None

    def get(self) -> bytes:
        return self.open().read()

    def open(self) -> IO[bytes]:
        if self.url:
            return get_url_reader(self.url, self._context).open()
        else:
            return get_stream(self.url + 'data')

    def copy_from(self, original: ResourceValue) -> None:
        raise Exception('Unsupported')

    def as_url(self):
        return UrlValueFromMemory('data:' + base64.b64encode(self.get()))


class HttpArchiveEntry(ArchiveEntry):

    def __init__(self, archive: 'HttpArchiveValue', name: str):
        self._archive = archive
        self._name = name

    def open(self) -> IO[bytes]:
        return get_url_reader(self._archive.entries_endpoint + self.name, self._archive.context).open()

    @property
    def name(self) -> str:
        return self._name


class HttpArchiveValue(ArchiveValue):

    def __init__(self, value_endpoint: str, context: Any=None):
        self._value_endpoint = value_endpoint.rstrip('/') + '/'
        self._context = context

    @property
    def context(self):
        return self._context

    @property
    def value_endpoint(self):
        return self._value_endpoint

    @property
    def entries_endpoint(self):
        if self.url is not None:
            return self.url.rstrip('/') + '/entries/'
        else:
            return self.value_endpoint.rstrip('/') + '/entries/'

    @property
    def url(self) -> Union[str, None]:
        if get_string(self.value_endpoint + 'subtype') == 'url':
            return get_string(self.value_endpoint + 'url')
        else:
            return None

    def get_entry(self, name: str) -> ArchiveEntry:
        # FIXME: here we don't check if the entry really exists
        return HttpArchiveEntry(self, name)

    @property
    def entries(self) -> List[ArchiveEntry]:
        return get_json(self.entries_endpoint)

    def open(self) -> IO[bytes]:
        return get_stream(self.value_endpoint + 'data')

    def get(self) -> Editor:
        raise NotImplemented("Not implemented")


class HttpPlainObjectValue(PlainObjectValue):

    def __init__(self, url: str) -> None:
        self._url = url.rstrip('/') + '/'

    def get(self) -> PlainObjectValue:  # type: ignore
        return get_json(self._url + 'data')

    def copy_from(self, original: PlainObjectValue) -> None:
        raise Exception('Unsupported')


class HttpArgument(Argument):

    def __init__(self, url: str, name: str) -> None:
        self._url = url.rstrip('/') + '/'
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def value(self) -> Value:
        return get_value_from_url(self._url)


def get_value_from_url(url: str) -> Value:

    url = url.rstrip('/') + '/'

    type_name = get_string(url + 'type')

    if type_name == ValueType.RESOURCE:
        return HttpResourceValue(url)
    elif type_name == ValueType.STRING:
        return HttpStringValue(url)
    elif type_name == ValueType.PLAIN_OBJECT:
        return HttpPlainObjectValue(url)
    elif type_name == ValueType.URL:
        return HttpUrlValue(url)
    else:
        raise Exception("Unsupported value type")


def serve_value(value: Value, path: str):

    if path == 'type':

        return value.type

    else:

        if value.type == ValueType.STRING or \
           value.type == ValueType.URL or \
           value.type == ValueType.PLAIN_OBJECT:

            if path != 'data':
                raise Exception("Invalid path")

            return value.get()

        elif isinstance(value, ResourceValue):

            if path == 'subtype':

                if value.url is not None:
                    return 'url'
                else:
                    return 'inline'

            elif path == 'url':

                if value.url is not None:
                    return value.url
                else:
                    return value.open()

        elif isinstance(value, ArchiveValue):

            if path == 'subtype':

                if value.url is not None:
                    return 'url'
                else:
                    return 'inline'

            elif path == 'url':
                return value.url

            elif path == 'entries':
                return [entry.name for entry in value.entries]

            elif path == 'data':
                return value.open()

            elif path.startswith('entries'):
                entry_name = path[len('entries/')]
                return value.get_entry(entry_name).open()

        else:
            raise Exception("Unsupported type of value")
