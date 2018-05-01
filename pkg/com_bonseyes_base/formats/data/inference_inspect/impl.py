from com_bonseyes_base.formats.data.database.format import DatabaseFormat
from com_bonseyes_base.formats.metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from ..database.api import Dataset, DatabaseEditor, DatabaseViewer
from ....lib.impl.formats.extended import ExtendedViewer, ExtendedEditor, ExtendedFormat
from ..inference_inspect.api import InferenceInspectViewer, InferenceInspectEditor, \
    INFERENCE_INSPECT_DATA_FORMAT_NAME, LayerData


class LayerDataImpl(LayerData):
    @property
    def layer_name(self) -> str:
        pass

    @property
    def layer_type(self) -> int:
        pass

    @property
    def layout(self) -> int:
        pass

    @property
    def data_type(self) -> int:
        pass

    @property
    def frac_bits(self) -> int:
        pass

    @property
    def output(self) -> Dataset:
        return self._parent.datasets.get('output')
        pass


class InferenceInspectViewerImpl(InferenceInspectViewer, ExtendedViewer[DatabaseViewer]):
    pass


class InferenceInspectEditorImpl(InferenceInspectEditor, ExtendedEditor[DatabaseEditor]):
    pass


class InferenceInspectFormat(ExtendedFormat):
    def __init__(self):
        ExtendedFormat.__init__(self, type_name=INFERENCE_INSPECT_DATA_FORMAT_NAME,
                                metadata_type=SIMPLE_METADATA_FORMAT_NAME,
                                base_format=DatabaseFormat(),
                                extended_viewer_factory=InferenceInspectViewerImpl,
                                extended_editor_factory=InferenceInspectEditorImpl)
