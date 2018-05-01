from typing import Dict

from ....lib.api.utils import MemoryNamedObjectMap, NamedObjectMap
from ....lib.impl.formats.http import HttpDataViewer
from .api import CompositeViewer, ComponentViewer
from .utils import ComponentViewerImpl


class HttpCompositeViewer(CompositeViewer, HttpDataViewer):

    def __init__(self, url: str, components: Dict[str, str]):
        HttpDataViewer.__init__(self, url.rstrip('/') + '/')

        part_viewers = {}

        for part_name, part_format in components.items():
            part_viewers[part_name] = ComponentViewerImpl(part_name,
                                                          self._url + part_name.lstrip('/') + '/',
                                                          part_format)

        self._components = MemoryNamedObjectMap(part_viewers)

    @property
    def components(self) -> NamedObjectMap[ComponentViewer]:
        return self._components
