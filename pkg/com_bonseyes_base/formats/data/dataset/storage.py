from typing import Dict, Any, IO

import json

from com_bonseyes_base.formats.data.dataset.api import EditableSample
from com_bonseyes_base.lib.api.values import StringValue, UrlValue, PlainObjectValue, ArchiveValue, ResourceValue
from ....lib.api.storage import Storage, Editor
from ....lib.api.utils import NamedObjectMap, create_data_views_from_dict, NamedObject, MemoryNamedObjectMap
from ....lib.api.values import Value
from ....lib.impl.utils import TarBuilder, TarBuilderReader
from ....lib.impl.values.memory_values import PlainObjectValueFromMemory, ResourceValueFromBlob
from .api import Datum, Sample, DataSetViewer, DataSetEditor


class MemoryDatum(Datum):

    def __init__(self, name: str, value: Value, sample: Sample):
        self._name = name
        self._value = value
        self._sample = sample

    @property
    def name(self):
        return self._name

    def value(self) -> Value:
        return self._value

    @property
    def sample(self) -> 'Sample':
        return self._sample


class StoredSample(Sample, NamedObject):

    def __init__(self, name: str, storage: Storage, sample_data: Dict):
        self._storage = storage
        self._name = name

        data = {}

        for aspect_name, aspect_value in sample_data.get('data', {}).items():
            data[aspect_name] = MemoryDatum(aspect_name,
                                            ResourceValueFromBlob(storage.get_stored_blob(aspect_value)), self)

        for aspect_name, aspect_value in sample_data.get('views', {}).items():
            data[aspect_name] = MemoryDatum(aspect_name,
                                            ResourceValueFromBlob(storage.get_stored_blob(aspect_value)), self)

        for aspect_name, aspect_value in sample_data.get('annotations', {}).items():
            data[aspect_name] = MemoryDatum(aspect_name, PlainObjectValueFromMemory(aspect_value), self)

        self._data = MemoryNamedObjectMap(data)

    def name(self) -> str:
        return self._name

    @property
    def data(self) -> NamedObjectMap[Datum]:
        return self._data


class StoredDataSetViewer(DataSetViewer):

    def __init__(self, storage: Storage):
        self._storage = storage

    def _get_sample(self, name: str, data: Any) -> StoredSample:
        return StoredSample(name, self._storage, data)

    @property
    def samples(self) -> NamedObjectMap[Sample]:

        with self._storage.open('dataset.json', mode='r') as fp:
            data_set = json.load(fp)

        return create_data_views_from_dict(data_set, self._get_sample)

    @property
    def dataset_json(self) -> Dict:
        with self._storage.open('dataset.json', 'r') as fp:
            return json.load(fp)

    def open_blob(self, name: str) -> IO[bytes]:
        return self._storage.open(name, 'rb')

    @property
    def url(self) -> str:
        return self._storage.url

    def as_stream(self) -> IO[bytes]:
        tar_builder = TarBuilder(self._storage)
        return TarBuilderReader(tar_builder)

    @property
    def storage(self):
        return self._storage


class StoredDataSetEditor(DataSetEditor):

    def __init__(self, storage: Storage):
        self._storage = storage
        self._samples = None

    def start(self):
        self._storage.makedirs('/', exist_ok=True)

        if self._storage.exists('dataset.json'):
            with self._storage.open('dataset.json', 'r') as fp:
                self._samples = json.load(fp)
        else:
            self._samples = {}

    def commit(self):
        with self._storage.open('dataset.json', 'w') as fp:
            json.dump(self._samples, fp)

    def edit_content(self) -> Editor:
        self._storage.makedirs('/', exist_ok=True)
        return self._storage.edit('/')

    def add_sample(self, name: str) -> EditableSample:
        data = {}
        self._samples[name] = data
        return StoredEditableSample(name, data, self._storage)


class StoredEditableSample(EditableSample):

    def __init__(self, name: str, data: Dict, storage: Storage):
        self._data = data
        self._storage = storage
        self._name = name

    def add_datum(self, name: str, value: Value):

        if isinstance(value, StringValue) or isinstance(value, UrlValue) or isinstance(value, PlainObjectValue):

            if 'annotations' not in self._data:
                self._data['annotations'] = {}

            self._data['annotations'][name] = value.get()

        elif isinstance(value, ArchiveValue) or isinstance(value, ResourceValue):

            file_name = self._name + '_' + name

            with self._storage.open(file_name, 'wb') as fp:
                fp.write(value.get())

            if 'data' not in self._data:
                self._data['data'] = {}

            self._data['data'][name] = file_name

        else:
            raise Exception("Unsupported type of value " + str(type(value)))
