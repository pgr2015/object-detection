from abc import ABCMeta, abstractmethod

from ....lib.api.data import DataViewer, DataEditor
from ....lib.api.storage import StoredBlob

BLOB_DATA_FORMAT_NAME = 'com.bonseyes.data.blob.0.1'


class BlobDataViewer(DataViewer, metaclass=ABCMeta):
    pass


class BlobDataEditor(DataEditor, metaclass=ABCMeta):

    @property
    @abstractmethod
    def stored_blob(self) -> StoredBlob:
        pass
