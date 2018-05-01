import json
from typing import Union, IO, Any, List

import base64
from shutil import copyfileobj

from ...api.storage import Storage, StoredNamedObject, Editor
from ...api.urls import get_url_reader
from ...api.values import StringValue, ValueType, ResourceValue, PlainObjectValue, Value, UrlValue, Argument, \
    ArchiveEntry, ArchiveValue
from ..values.memory_values import PlainObjectValueFromMemory, ResourceValueFromMemory, \
    UrlValueFromMemory, \
    StringValueFromMemory, ArchiveValueFromStorage, ArchiveValueFromUrl


class FileStringValue(StringValue):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    @property
    def name(self) -> str:
        return self._storage.name

    def get(self) -> str:
        with self._storage.open('/value', mode='r') as fp:
            return fp.read()

    def copy_from(self, original: StringValue) -> None:

        with self._storage.open('/value', mode='w') as fp:
            fp.write(original.get())

        with self._storage.open('/type', mode='w') as fp:
            fp.write(ValueType.STRING)

    def as_plain_object(self):
        return PlainObjectValueFromMemory(self.get())

    def as_resource(self):
        return ResourceValueFromMemory(url=self.get())

    def as_url(self):
        return UrlValueFromMemory(self.get())


class FileUrlValue(UrlValue):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    @property
    def name(self) -> str:
        return self._storage.name

    def get(self) -> str:
        with self._storage.open('/value', mode='r') as fp:
            return fp.read()

    def copy_from(self, original: UrlValue) -> None:

        with self._storage.open('/value', mode='w') as fp:
            fp.write(original.get())

        with self._storage.open('/type', mode='w') as fp:
            fp.write(ValueType.URL)

    def as_string(self):
        return StringValueFromMemory(self.get())

    def as_plain_object(self):
        return PlainObjectValueFromMemory(self.get())

    def as_resource(self):
        return ResourceValueFromMemory(url=self.get())

    def as_archive(self) -> 'ArchiveValue':
        raise ArchiveValueFromUrl(self.get())


class FileResourceValue(ResourceValue):

    def __init__(self, storage: Storage, context: Any=None) -> None:
        self._storage = storage
        self._context = context

    @property
    def name(self) -> str:
        return self._storage.name

    @property
    def url(self) -> Union[str, None]:
        if not self._storage.exists('url'):
            return None

        with self._storage.open('url', 'r') as fp:
            return fp.read()

    def _download_if_necessary(self) -> None:
        if self._storage.exists('data'):
            return

        if self._storage.exists('cache'):
            return

        if self.url is None:
            raise ValueError('Resource parameter without value and url')

        fpi = get_url_reader(self.url, self._context).open()

        try:

            with self._storage.open('cache', 'wb') as fpo:
                copyfileobj(fpi, fpo)

        except Exception:
            self._storage.delete('cache')
            raise
        finally:
            fpi.close()

    def _get_data_path(self) -> str:
        if self._storage.exists('/data'):
            return '/data'
        else:
            return '/cache'

    def get(self) -> bytes:
        self._download_if_necessary()

        with self._storage.open(self._get_data_path(), 'rb') as fp:
            return fp.read()

    def open(self) -> IO[bytes]:
        self._download_if_necessary()

        return self._storage.open(self._get_data_path(), 'rb')

    def edit(self) -> Editor:
        self._download_if_necessary()

        return self._storage.edit(self._get_data_path())

    def copy_from(self, original: ResourceValue) -> None:

        self._storage.makedirs('/', exist_ok=True)

        # TODO: here we could potentially copy the whole cached data

        with self._storage.open('/type', mode='w') as fp:
            fp.write(ValueType.RESOURCE)

        if original.url is not None:

            with self._storage.open('/url', 'w') as fp:
                fp.write(original.url)

        else:

            with self._storage.open('/data', 'wb') as fpo:
                with original.open() as fpi:
                    copyfileobj(fpi, fpo)

    def as_url(self):
        return UrlValueFromMemory('data:' + base64.b64encode(self.get()))


class FilePlainObjectValue(PlainObjectValue):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    @property
    def name(self) -> str:
        return self._storage.name

    def get(self) -> PlainObjectValue:  # type: ignore
        with self._storage.open('/value', mode='r') as fp:
            # TODO: check that we are reading something correct here
            return json.load(fp)

    def copy_from(self, original: PlainObjectValue) -> None:

        self._storage.makedirs('/', exist_ok=True)

        # TODO: here we could avoid parsing the data if we know the value
        # we parse is a SimpleJsonValue

        with self._storage.open('/type', mode='w') as fp:
            fp.write(ValueType.PLAIN_OBJECT)

        with self._storage.open('/value', mode='w') as fp:
            json.dump(original.get(), fp)


class FileArchiveValue(ArchiveValue):

    def __init__(self, storage: Storage):
        self._storage = storage

    @property
    def name(self) -> str:
        return self._storage.name

    def copy_from(self, original: ArchiveValue) -> None:

        with self._storage.open('/type', mode='w') as fp:
            fp.write(ValueType.ARCHIVE)

        if original.url is not None:

            with self._storage.open('/url', 'w') as fp:
                fp.write(original.url)

        else:

            for entry in original.entries:
                with self._storage.open('/data/' + entry.name, 'wb') as fpo:
                    with entry.open() as fpi:
                        copyfileobj(fpi, fpo)

    def _get_subvalue(self) -> ArchiveValue:
        if self.url is not None:
            return ArchiveValueFromStorage(self._storage.get_substorage('data'))
        else:
            return ArchiveValueFromUrl(self.url)

    def get_entry(self, name: str) -> ArchiveEntry:
        return self._get_subvalue().get_entry(name)

    def get(self) -> 'Editor':
        return self._get_subvalue().get()

    def open(self) -> IO[bytes]:
        return self._get_subvalue().open()

    @property
    def url(self) -> Union[str, None]:
        if not self._storage.exists('url'):
            return None

        with self._storage.open('url', 'r') as fp:
            return fp.read()

    @property
    def entries(self) -> List[ArchiveEntry]:
        return self._get_subvalue().entries


class StoredArgument(Argument, StoredNamedObject):

    def __init__(self, storage: Storage):
        StoredNamedObject.__init__(self, storage)

    def create(self, value: Value):
        value_storage = self._storage.get_substorage('value')
        put_value_to_storage(value, value_storage)

    @property
    def value(self) -> Value:
        value_storage = self._storage.get_substorage('value')
        return get_value_from_storage(value_storage)


def get_value_from_storage(storage: Storage) -> Value:

    if not storage.exists('/type'):
        raise ValueError('Missing type for value')

    with storage.open('/type', 'r') as fp:
        type_name = fp.read()

    if type_name == ValueType.RESOURCE:
        return FileResourceValue(storage)
    elif type_name == ValueType.ARCHIVE:
        return FileArchiveValue(storage)
    elif type_name == ValueType.STRING:
        return FileStringValue(storage)
    elif type_name == ValueType.PLAIN_OBJECT:
        return FilePlainObjectValue(storage)
    elif type_name == ValueType.URL:
        return FileUrlValue(storage)
    else:
        raise ValueError('Unsupported value type %s found in storage %s' % (type_name, storage.name))


def put_value_to_storage(value: Value, storage: Storage) -> Value:

    if isinstance(value, StringValue):
        dest_value = FileStringValue(storage)
        dest_value.copy_from(value)
    elif isinstance(value, PlainObjectValue):
        dest_value = FilePlainObjectValue(storage)
        dest_value.copy_from(value)
    elif isinstance(value, ResourceValue):
        dest_value = FileResourceValue(storage)
        dest_value.copy_from(value)
    elif isinstance(value, ArchiveValue):
        dest_value = FileArchiveValue(storage)
        dest_value.copy_from(value)
    elif isinstance(value, UrlValue):
        dest_value = FileUrlValue(storage)
        dest_value.copy_from(value)
    else:
        raise ValueError("Cannot store value of type " + str(type(value)))

    return dest_value
