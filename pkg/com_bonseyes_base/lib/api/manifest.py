from typing import Dict, Optional

from .runtime import ImageConfig, get_image_config_from_dict
from .storage import StorableObject
from .utils import NamedObjectMap, create_data_views_from_dict, NamedDataView


class Parameter(NamedDataView):

    @property
    def type(self) -> str:
        return self._data.get('type', 'string')

    @property
    def label(self) -> str:
        return self._data.get('label', None)

    @property
    def data_format(self) -> str:
        return self._data.get('data_format', None)

    @property
    def optional(self) -> bool:
        return self._data.get('optional', False)


class MetricDescription(NamedDataView):

    @property
    def metric_type(self) -> str:
        return self._data['type']

    @property
    def label(self) -> Optional[str]:
        return self._data.get('label')


class ActionDescription(NamedDataView):

    @property
    def parameters(self):
        return create_data_views_from_dict(self._data.get('parameters', {}), Parameter)

    @property
    def description(self) -> Optional[str]:
        return self._data.get('description')

    @property
    def metrics(self) -> NamedObjectMap[MetricDescription]:
        return create_data_views_from_dict(self._data.get('metrics', {}), MetricDescription)


class Manifest(StorableObject):

    def __init__(self, data: Dict) -> None:
        self._data = data

    @property
    def output_data_format(self) -> str:
        return self._data['output']['data_format']

    @property
    def description(self) -> Optional[str]:
        return self._data.get('description', None)

    @property
    def actions(self) -> NamedObjectMap[ActionDescription]:
        return create_data_views_from_dict(self._data.get('actions', {}), ActionDescription)

    @property
    def image_config(self) -> Optional[ImageConfig]:

        if 'image' not in self._data:
            return None

        return get_image_config_from_dict(self._data['image'])

    def to_dict(self):
        return self._data
