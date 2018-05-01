import json

import cbor
from flask import request

from ....lib.impl.formats.http import DataServerBase
from ..database.api import Dataset, DatabaseViewer


def get_volume(dataset: Dataset):

    volume = []

    if 'volume' not in request.args:
        return dataset[tuple(volume)].tolist()

    for dimensions in request.args.get('volume').split(','):

        if ':' not in dimensions:
            volume.append(int(dimensions))
        else:
            start, step, stop = dimensions.split(':')

            volume.append(slice(int(start) if start != '' else None,
                                int(stop) if stop != '' else None,
                                int(step) if step != '' else None))

    return dataset[tuple(volume)]


class DatabaseServer(DataServerBase[DatabaseViewer]):

    def _get_subpath(self, data: DatabaseViewer, path: str):

        with data:

            if path == 'datasets/':
                return data.datasets.names

            elif path.startswith('datasets/'):
                dataset = path[len('datasets'):path.rfind('/')]
                sub_path = path[path.rfind('/')+1:]
                dataset_obj = data.datasets.get(dataset)

                if sub_path == 'data':

                    format_name = request.args.get('format', 'json')

                    data = get_volume(dataset_obj)

                    if format_name == 'json':
                        return json.dumps({'shape': data.shape, 'data': data.reshape(-1).tolist()})

                    elif format_name == 'cbor':
                        return cbor.dumps({'shape': data.shape, 'data': data.reshape(-1).tolist()})

                elif sub_path == 'dimensions':
                    return [{'name': dim.name, 'size': dim.size} for dim in dataset_obj.dimensions.all]

                elif sub_path == 'data_format':
                    return dataset_obj.data_type
                else:
                    raise Exception("Invalid path")

            else:
                raise Exception("Invalid path")
