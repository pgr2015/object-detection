"""

Implementation of values abstract classes that use memory
as backing store.

"""
import base64
import tarfile
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from typing import Union, IO, Optional, Any, List, Callable

from io import BytesIO

import os

from ...api.storage import Editor, StoredBlob
from ...api.storage import Storage
from ...api.urls import get_url_reader
from ...api.values import StringValue, ResourceValue, PlainObjectValue, PlainObjectType, UrlValue, ArchiveValue, \
    ArchiveEntry
from ..rpc.http_rpc_client import get_stream
from ..storage.file_storage import FileStorage
from ..utils import TarBuilderReader, TarStream, TarBuilder


class StringValueFromMemory(StringValue):
    """
    Stores a string in memory
    """

    def __init__(self, data: str) -> None:
        self._data = data

    def get(self) -> str:
        return self._data

    def copy_from(self, original: StringValue) -> None:
        self._data = original.get()

    def as_plain_object(self):
        return PlainObjectValueFromMemory(self._data)

    def as_resource(self):
        return ResourceValueFromMemory(url=self._data)

    def as_url(self):
        return UrlValueFromMemory(self._data)


class UrlValueFromMemory(UrlValue):
    """
    Stores an URL in memory
    """

    def __init__(self, data: str) -> None:
        self._data = data

    def get(self) -> str:
        return self._data

    def copy_from(self, original: UrlValue) -> None:
        self._data = original.get()

    def as_string(self):
        return StringValueFromMemory(self._data)

    def as_plain_object(self):
        return PlainObjectValueFromMemory(self._data)

    def as_resource(self):
        return ResourceValueFromMemory(url=self._data)

    def as_archive(self):
        return ArchiveValueFromUrl(url=self._data)


class ResourceValueFromFile(ResourceValue):
    """
    Wraps the contents of a local file as a resource
    """

    def __init__(self, path: Optional[bytes]=None) -> None:
        self._path = path

    @property
    def url(self) -> Union[str, None]:
        return None

    def get(self) -> bytes:
        with open(self._path, 'rb') as fp:
            return fp.read()

    def open(self) -> IO[bytes]:
        return open(self._path, 'rb')

    def copy_from(self, original: ResourceValue) -> None:
        raise NotImplemented("Resource value from file is immutable")

    def as_url(self):
        return UrlValueFromMemory('data:' + base64.b64encode(self.get()))


class ResourceValueFromStream(ResourceValue):
    """
    Wraps a stream as a resource
    """

    def __init__(self, stream: IO[bytes]) -> None:
        self._stream = stream

    @property
    def url(self) -> Union[str, None]:
        return None

    def get(self) -> bytes:
        return self._stream.read()

    def open(self) -> IO[bytes]:
        return self._stream

    def copy_from(self, original: ResourceValue) -> None:
        raise NotImplemented("Resource value from file is immutable")

    def as_url(self):
        return UrlValueFromMemory('data:' + base64.b64encode(self.get()))


class ResourceValueFromMemory(ResourceValue):
    """
    Stores a resource in memory. The resource data can be either retrieved
    from a URL or be stored in memory.
    """

    def __init__(self, url: Optional[str]=None, data: Optional[bytes]=None, context: Any=None) -> None:
        self._url = url
        self._data = data
        self._context = context
        self._cache = None  # type: Optional[bytes]

    @property
    def url(self) -> Union[str, None]:
        return self._url

    def _download_if_necessary(self) -> None:
        if self._data is not None:
            return

        if self._cache is not None:
            return

        if self.url is None:
            raise ValueError('Resource parameter without value and url')

        try:

            self._cache = get_url_reader(self._url, self._context).open().read()

        except Exception:
            self._cache = None
            raise

    def get(self) -> bytes:
        if self._data is not None:
            return self._data
        else:
            self._download_if_necessary()
            return self._cache

    def open(self) -> IO[bytes]:
        return BytesIO(self.get())

    def copy_from(self, original: ResourceValue) -> None:

        if original.url is None:
            self._data = original.get()
        else:
            self._url = original.url

    def as_url(self):
        if self._url is not None:
            return UrlValueFromMemory(self._url)
        else:
            return UrlValueFromMemory('data:' + base64.b64encode(self.get()))

    def as_archive(self) -> 'ArchiveValue':
        if self.url:
            return ArchiveValueFromUrl(self.url)
        else:
            raise Exception("Impossible to cast in-place resource to archive")


class ResourceValueFromUrl(ResourceValueFromMemory):
    def __init__(self, url: str, context: Any = None):
        ResourceValueFromMemory.__init__(self, url=url, context=context)


class ResourceValueFromBlob(ResourceValue):

    def __init__(self, blob: StoredBlob):
        self._blob = blob

    @property
    def url(self) -> Union[str, None]:
        return None

    def get(self) -> bytes:
        with self._blob.open('rb') as fp:
            return fp.read()

    def open(self) -> IO[bytes]:
        return self._blob.open('rb')

    def edit(self) -> Editor:
        return self._blob.edit()

    def as_url(self):
        return UrlValueFromMemory('data:' + base64.b64encode(self.get()))


class ArchiveEntryFromStorage(ArchiveEntry):

    def __init__(self, storage: Storage, name: str):
        self._name = name
        self._storage = storage

    def open(self) -> IO[bytes]:
        return self._storage.open(self._name, mode='rb')

    @property
    def name(self) -> str:
        return self._name


class ArchiveValueFromStorage(ArchiveValue):

    def __init__(self, storage: Storage):
        self._storage = storage

    def copy_from(self, value: 'ArchiveValue') -> None:
        for entry in value.entries:
            with self._storage.open(entry.name, 'wb') as fpo:
                with entry.open() as fpi:
                    copyfileobj(fpi, fpo)

    def get_entry(self, name: str) -> ArchiveEntry:

        if not self._storage.exists(name):
            raise KeyError("Entry doesn't exist")

        return ArchiveEntryFromStorage(self._storage, name)

    def get(self) -> 'Editor':
        return self._storage.edit('/')

    def open(self) -> IO[bytes]:
        builder = TarBuilder(self._storage)
        return TarBuilderReader(builder)

    @property
    def url(self) -> Union[str, None]:
        return None

    @property
    def entries(self) -> List[ArchiveEntry]:
        for entry in self._storage.entries:
            yield ArchiveEntryFromStorage(self._storage, entry.name)


class ArchiveValueFromDirectory(ArchiveValueFromStorage):

    def __init__(self, path: str):
        ArchiveValueFromStorage.__init__(self, FileStorage(path))


class ArchiveEntryFromMemory(ArchiveEntry):

    def __init__(self, data: bytes, name: str):
        self._data = data
        self._name = name

    def open(self) -> IO[bytes]:
        return BytesIO(self._data)

    @property
    def name(self) -> str:
        return self._name


class ArchiveEditorFromStream(Editor):

    def __init__(self, stream: IO[bytes]):
        self._tempdir = None
        self._stream = stream

    def open(self) -> str:
        self._tempdir = TemporaryDirectory()

        try:

            archive_dataset = tarfile.open(fileobj=TarStream(self._stream), mode="r:")

            for tar_entry in archive_dataset:
                with open(os.path.join(self._tempdir.name, tar_entry.name), 'wb') as fpo:
                    with tar_entry.open('rb') as fpi:
                        copyfileobj(fpi, fpo)

        except:
            self._tempdir.cleanup()
            raise

        return self._tempdir.name

    def close(self) -> None:
        self._tempdir.cleanup()


class ArchiveValueFromStreamGenerator(ArchiveValue):

    def __init__(self, stream_generator: Callable[[], IO[bytes]]):
        self._stream_generator = stream_generator

    def get_entry(self, name: str) -> ArchiveEntry:
        archive_dataset = tarfile.open(fileobj=TarStream(self._stream_generator()), mode="r:")

        for tar_entry in archive_dataset:
            entry_name = tar_entry.name.lstrip('./')

            if entry_name != name:
                continue

            with tar_entry.open() as fp:
                return ArchiveEntryFromMemory(fp.read(), entry_name)

    def get(self) -> 'Editor':
        return ArchiveEditorFromStream(self._stream_generator())

    def open(self) -> IO[bytes]:
        return self._stream_generator()

    @property
    def url(self) -> Union[str, None]:
        return None

    @property
    def entries(self) -> List[ArchiveEntry]:
        tar = tarfile.open(fileobj=TarStream(self._stream_generator()), mode="r:")

        for tar_entry in tar:
            entry_name = tar_entry.name.lstrip('./')

            with tar.extractfile(tar_entry) as fp:
                yield ArchiveEntryFromMemory(fp.read(), entry_name)


class ArchiveValueFromUrl(ArchiveValueFromStreamGenerator):

    def __init__(self, url: str):
        self._url = url
        ArchiveValueFromStreamGenerator.__init__(self, lambda: get_stream(self._url))

    @property
    def url(self) -> Union[str, None]:
        return self._url


class ArchiveValueFromStream(ArchiveValueFromStreamGenerator):

    def __init__(self, stream: IO[bytes]):
        ArchiveValueFromStreamGenerator.__init__(self, lambda: stream)


class PlainObjectValueFromMemory(PlainObjectValue):
    """
    Wraps a plain object stored in memory.
    """

    def __init__(self, data: PlainObjectType) -> None:
        self._data = data

    def get(self) -> PlainObjectType:
        return self._data

    def copy_from(self, original: PlainObjectValue) -> None:
        self._data = original.get()
