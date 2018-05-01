from ....lib.api.data import DataViewer, data_formats, DataEditor
from .api import ComponentViewer, ComponentEditor


class ComponentViewerImpl(ComponentViewer):

    def __init__(self, name: str, url: str, format_name: str):
        self._url = url
        self._name = name
        self._format = format_name

    @property
    def viewer(self) -> DataViewer:
        return data_formats.get(self._format).get_viewer(self._url)

    @property
    def name(self) -> str:
        return self._name


class ComponentEditorImpl(ComponentEditor):

    def __init__(self, name: str, url: str, format_name: str):
        self._url = url
        self._name = name
        self._format = format_name

    @property
    def editor(self) -> DataEditor:
        return data_formats.get(self._format).get_editor(self._url)

    @property
    def name(self) -> str:
        return self._name
