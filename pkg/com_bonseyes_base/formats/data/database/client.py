import cbor
import numpy
import numpy as np

from ....lib.api.storage import Editor
from ....lib.api.utils import OrderedNamedObjectList, MemoryOrderedObjectList, NamedObjectMap, MemoryNamedObjectMap
from ....lib.impl.formats.http import HttpDataViewer
from ....lib.impl.rpc.http_rpc_client import get_json, get_stream, get_string
from ....lib.impl.storage.http_storage import HttpStoredBlob
from ..database.api import DatabaseViewer, Dataset, Dimension, DataType, Attribute


class HttpDataset(Dataset):

    def __init__(self, name: str, url: str):
        self._name = name
        self._url = url.rstrip('/') + '/'

    @property
    def name(self):
        return self._name

    def __getitem__(self, item) -> numpy.ndarray:

        query = []

        if isinstance(item, int):
            query.append(str(item))
        elif isinstance(item, slice):

            start = str(item.start) if item.start is not None else ''
            step = str(item.step) if item.step is not None else ''
            end = str(item.stop) if item.stop is not None else ''

            query.append(start+':' + step + ':' + end)

        elif isinstance(item, list):
            for x in item:
                query.append(str(x))
        elif isinstance(item, tuple):

            for dim_range in item:

                if isinstance(dim_range, slice):
                    start = str(dim_range.start) if dim_range.start is not None else ''
                    step = str(dim_range.step) if dim_range.step is not None else ''
                    end = str(dim_range.stop) if dim_range.stop is not None else ''
                elif isinstance(dim_range, int):
                    start = str(dim_range)
                    step = ''
                    end = str(dim_range + 1)
                else:
                    raise Exception("Unsupported range")
                query.append(start+':' + step + ':' + end)

        else:
            raise Exception("Unsupported index")

        with get_stream(self._url + 'data?format=cbor&volume=' + ",".join(query)) as fp:
            data = fp.read()

        volume = cbor.loads(data)

        data = np.array(volume['data'], dtype=DataType.to_numpy_dtype(self.data_type))

        return data.reshape(volume['shape'])

    @property
    def dimensions(self) -> OrderedNamedObjectList[Dimension]:

        dimensions = [Dimension(x['name'], idx, x['size'])
                      for idx, x in enumerate(get_json(self._url + 'dimensions'))]

        return MemoryOrderedObjectList(dimensions)

    @property
    def data_type(self) -> str:
        return get_string(self._url + 'data_format')

    @property
    def attributes(self) -> NamedObjectMap[Attribute]:
        raise NotImplemented()


class HttpDatabaseViewer(DatabaseViewer, HttpDataViewer):

    @property
    def datasets(self) -> NamedObjectMap[HttpDataset]:
        dataset_names = get_json(self._url + 'datasets/')
        return MemoryNamedObjectMap({x: HttpDataset(x, self._url + 'datasets/' + x + '/') for x in dataset_names})

    def view_content(self) -> Editor:
        return HttpStoredBlob(self._url).edit()


