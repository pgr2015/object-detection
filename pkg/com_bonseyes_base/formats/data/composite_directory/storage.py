from typing import Dict, IO

from ....lib.api.storage import Storage, Editor
from ....lib.api.utils import MemoryNamedObjectMap, NamedObjectMap
from ....lib.impl.utils import TarBuilder, TarBuilderReader
from .api import CompositeViewer, CompositeEditor, ComponentViewer, ComponentEditor
from .utils import ComponentViewerImpl, ComponentEditorImpl


class StoredCompositeViewer(CompositeViewer):

    def __init__(self, components: Dict[str, str], storage: Storage) -> None:

        self._storage = storage

        part_viewers = {}

        for part_name, part_format in components.items():
            part_viewers[part_name] = ComponentViewerImpl(part_name,
                                                          self._storage.get_substorage(part_name).url,
                                                          part_format)

        self._components = MemoryNamedObjectMap(part_viewers)

    def as_stream(self) -> IO[bytes]:
        tar_builder = TarBuilder(self._storage)
        return TarBuilderReader(tar_builder)

    @property
    def url(self) -> str:
        return self._storage.url

    @property
    def components(self) -> NamedObjectMap[ComponentViewer]:
        return self._components


class StoredCompositeEditor(CompositeEditor):

    def __init__(self, components: Dict[str, str], storage: Storage) -> None:

        self._storage = storage

        part_editors = {}

        for part_name, part_format in components.items():
            part_editors[part_name] = ComponentEditorImpl(part_name,
                                                          self._storage.url.rstrip('/') + '/' + part_name,
                                                          part_format)

        self._components = MemoryNamedObjectMap(part_editors)

    @property
    def components(self) -> NamedObjectMap[ComponentEditor]:
        return self._components

    def start(self):
        super().start()
        self._storage.makedirs('/', exist_ok=True)

    @property
    def storage(self) -> Storage:
        return self._storage

    def edit_content(self) -> Editor:
        self._storage.makedirs('/', exist_ok=True)
        return self._storage.edit()
