from typing import Dict, Iterator, IO

import tarfile

from ....lib.api.utils import NamedObjectMap, create_data_views_from_dict, MemoryNamedObjectMap
from ....lib.api.values import Value
from ....lib.impl.formats.http import HttpDataViewer
from ....lib.impl.utils import TarStream
from ....lib.impl.values.memory_values import ResourceValueFromMemory, PlainObjectValueFromMemory
from ....lib.impl.rpc.http_rpc_client import get_stream, get_json
from .api import Datum, Sample, DataSetViewer


class HttpDatum(Datum):

    def __init__(self, sample: Sample, name: str, value: Value):
        self._value = value
        self._name = name
        self._sample = sample

    @property
    def sample(self) -> 'Sample':
        return self._sample

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value


class RelativeResourceValue(ResourceValueFromMemory):

    def __init__(self, base_url: str, relative_path: str):
        ResourceValueFromMemory.__init__(self, base_url + relative_path)
        self.relative_path = relative_path


class HttpSample(Sample):

    def __init__(self, url: str, name: str, sample_data: Dict):
        self._name = name

        data = {}

        base_url = url.rstrip('/') + '/'

        for aspect_name, aspect_value in sample_data.get('data', {}).items():
            data[aspect_name] = HttpDatum(self, aspect_name, RelativeResourceValue(base_url, aspect_value))

        for aspect_name, aspect_value in sample_data.get('views', {}).items():
            data[aspect_name] = HttpDatum(self, aspect_name, RelativeResourceValue(base_url, aspect_value))

        for aspect_name, aspect_value in sample_data.get('annotations', {}).items():
            data[aspect_name] = HttpDatum(self, aspect_name, PlainObjectValueFromMemory(aspect_value))

        self._data = MemoryNamedObjectMap(data)

    @property
    def name(self) -> str:
        return self._name

    @property
    def data(self) -> NamedObjectMap[HttpDatum]:
        return self._data


class HttpDataSetViewer(DataSetViewer, HttpDataViewer):

    @property
    def samples(self) -> NamedObjectMap[HttpSample]:
        dataset_json = get_json(self._url + 'dataset.json')
        return create_data_views_from_dict(dataset_json, lambda name, data: HttpSample(self._url, name, data))

    def open_blob(self, name: str) -> IO[bytes]:
        return get_stream(self._url + name)

    def stream_data(self, data_types: str) -> Iterator[Datum]:

        blob_to_sample = {}

        for sample in self.samples.all:

            for data_type in data_types:

                try:
                    value = sample.data.get(data_type).value   # type: HttpDatum

                    if not isinstance(value, RelativeResourceValue):
                        continue

                    blob_to_sample[value.relative_path] = (sample, data_type)

                except KeyError:
                    continue

        with get_stream(self._url) as fp:

            archive_dataset = tarfile.open(fileobj=TarStream(fp), mode="r:")

            for view in archive_dataset:

                view_name = view.name.lstrip('./')

                data_info = blob_to_sample.get(view_name)

                if data_info is None:
                    continue

                data = archive_dataset.extractfile(view).read()

                yield HttpDatum(data_info[0], data_info[1], ResourceValueFromMemory(data=data))

