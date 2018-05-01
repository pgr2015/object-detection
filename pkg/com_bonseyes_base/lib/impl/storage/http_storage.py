import os
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from typing import AnyStr, IO, List

from typing import TextIO
from urllib.parse import urlparse

import requests
from io import BytesIO

from ...api.storage import Storage, Editor, StorageEntry, StoredBlob
from ..rpc.http_rpc_client import get_stream


class HttpStorage(Storage):

    def __init__(self, url: str) -> None:
        self._url = url.rstrip('/')

    def _get_full_path(self, path: str) -> str:
        # FIXME: security: check that path is a child of data_dir
        return self.url + '/' + path.lstrip('/')

    @property
    def url(self):
        return self._url

    @property
    def name(self) -> str:
        (scheme, netloc, path, params, query, fragment) = urlparse(self.url)
        return path.strip('/').split('/')[-1]

    def open(self, path: str, mode: str) -> IO[AnyStr]:
        return self.get_stored_blob(path).open(mode)

    def exists(self, path: str) -> bool:
        return self.get_stored_blob(path).exists()

    def create_new_substorage(self) -> 'Storage':
        raise Exception("Unable to modify an HTTP storage")

    def makedirs(self, path: str, exist_ok: bool=False) -> None:
        raise Exception("Unable to modify an HTTP storage")

    def delete(self, path: str) -> None:
        raise Exception("Unable to modify an HTTP storage")

    def list(self, path: str) -> List[str]:
        raise Exception("Unable to list an HTTP storage")

    def isdir(self, path: str) -> bool:
        raise Exception("Unable to find dirs on HTTP storage")

    def edit(self, path: str) -> Editor:
        raise Exception("Unable to edit from HTTP storage")

    def get_substorage(self, path: str) -> 'Storage':
        substorage_path = self._get_full_path(path)
        return HttpStorage(substorage_path)

    def move(self, src_path: str, dst_path: str) -> None:
        raise Exception("Unable to move on HTTP storage")

    def copy(self, src_path: str, dst_path: str) -> None:
        raise Exception("Unable to copy on HTTP storage")

    @property
    def entries(self) -> List[StorageEntry]:
        raise Exception("Unable to enumerate on HTTP storage")

    def get_stored_blob(self, path: str) -> 'HttpStoredBlob':
        full_path = self._get_full_path(path)
        return HttpStoredBlob(full_path)


class HttpBlobEditor(Editor):
    def __init__(self, url: str):
        self._url = url
        self._temp_dir = None

    def open(self) -> str:

        self._temp_dir = TemporaryDirectory()

        try:

            file_name = os.path.join(self._temp_dir.name, 'data')

            with get_stream(self._url) as fpi:
                with open(file_name, 'wb') as fpo:
                    copyfileobj(fpi, fpo)

            return file_name

        except:
            self._temp_dir.cleanup()
            raise

    def close(self) -> None:
        self._temp_dir.cleanup()


class HttpStoredBlob(StoredBlob):

    def __init__(self, url: str):
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    def open(self, mode: str) -> IO:

        if mode not in ['r', 'rb']:
            raise Exception("Invalid mode " + mode)

        with requests.get(self._url) as ret:

            if ret.status_code == 404:
                raise FileNotFoundError("Cannot find path " + self._url)

            if ret.status_code != 200:
                raise Exception("Error while fetching path " + self._url)

            if mode == 'r':
                return TextIO(ret.text)
            else:
                return BytesIO(ret.content)

    @property
    def exists(self) -> bool:

        with requests.head(self._url) as ret:

            if ret.status_code == 404:
                return False

            if ret.status_code == 200:
                return True

            raise Exception("Error while checking path " + self._url)

    def edit(self) -> Editor:
        return HttpBlobEditor(self._url)
