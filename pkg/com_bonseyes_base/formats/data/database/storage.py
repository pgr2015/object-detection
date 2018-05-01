from typing import List, Optional, Tuple, IO, Any

import h5py

from ....lib.api.storage import Editor, StoredBlob
from ....lib.api.utils import MemoryOrderedObjectList, OrderedNamedObjectList, NamedObjectMap
from ..database.api import Dataset, Dimension, DataType, EditableDataset, DatabaseViewer, \
    DatabaseEditor, Attribute


class HDF5Dataset(EditableDataset):

    def __init__(self, dataset: h5py.Dataset):
        self._dataset = dataset

    @property
    def name(self):
        return self._dataset.name

    def __getitem__(self, item):
        return self._dataset[item][:]

    @property
    def data_type(self) -> str:
        return DataType.from_numpy_dtype(self._dataset.dtype)

    @property
    def dimensions(self) -> OrderedNamedObjectList[Dimension]:

        dimensions = []

        for idx in range(len(self._dataset.dims)):
            label = self._dataset.dims[idx].label
            size = self._dataset.shape[idx]

            dimension = Dimension(label, idx, size)

            dimensions.append(dimension)

        return MemoryOrderedObjectList(dimensions)
    
    def __setitem__(self, key, value):
        self._dataset[key] = value

    def resize(self, size: int, axis: int) -> None:
        self._dataset.resize(size, axis=axis)

    def set_attribute(self, name: str, value: Any, dtype: str):
        raise NotImplemented()

    @property
    def attributes(self) -> NamedObjectMap[Attribute]:
        raise NotImplemented()


class HDF5DatasetMap(NamedObjectMap[HDF5Dataset]):

    def __init__(self, file: h5py.File):
        self._file = file

    @property
    def all(self) -> List[HDF5Dataset]:
        return [self.get(x) for x in self.names]

    @property
    def names(self) -> List[str]:
        return [x for x in self._file.keys()]

    def get(self, name: str) -> HDF5Dataset:
        return HDF5Dataset(self._file[name])

    @property
    def count(self) -> int:
        return len(self._file)


class StoredDatabaseViewer(DatabaseViewer):

    def __init__(self, stored_blob: StoredBlob):
        self._stored_blob = stored_blob
        self._file = None   # type: h5py.File
        self._blob_editor = None    # type: Editor

    @property
    def url(self) -> str:
        return self._stored_blob.url

    @property
    def blob(self):
        return self._stored_blob

    def as_stream(self) -> IO[bytes]:
        return self._stored_blob.open('rb')

    def view_content(self) -> Editor:
        return self._stored_blob.edit()

    @property
    def datasets(self) -> NamedObjectMap[Dataset]:
        return HDF5DatasetMap(self._file)

    def open(self):
        self._blob_editor = self._stored_blob.edit()
        file_path = self._blob_editor.open()
        self._file = h5py.File(file_path, 'r')

    def close(self):
        self._file.close()
        self._blob_editor.close()


class StoredDatabaseEditor(DatabaseEditor):

    def __init__(self, stored_blob: StoredBlob):
        self._stored_blob = stored_blob
        self._file = None   # type: h5py.File
        self._blob_editor = None    # type: Editor

    @property
    def url(self) -> str:
        return self._stored_blob.url

    @property
    def blob(self):
        return self._stored_blob

    def add_dataset(self, name: str,
                    dimension_names: Optional[Tuple[str]],
                    shape: Tuple[int],
                    maxshape: Optional[Tuple[Optional[int]]],
                    data_type: str) -> EditableDataset:

        dtype = DataType.to_numpy_dtype(data_type)
        dataset = self._file.create_dataset(name, shape=shape, maxshape=maxshape, dtype=dtype)

        if dimension_names is not None:
            for idx, dimension_name in enumerate(dimension_names):
                dataset.dims.get(idx).label = dimension_name
        
        return HDF5Dataset(dataset)

    @property
    def datasets(self) -> NamedObjectMap[EditableDataset]:
        return HDF5DatasetMap(self._file)

    def start(self):
        self._blob_editor = self._stored_blob.edit()
        file_path = self._blob_editor.open()
        self._file = h5py.File(file_path, 'w')

    def commit(self):
        self._file.close()
        self._blob_editor.close()

    def edit_content(self) -> Editor:
        return self._stored_blob.edit()
