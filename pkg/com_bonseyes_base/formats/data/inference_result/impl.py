from com_bonseyes_base.formats.metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from ....lib.api.data import data_formats
from ..database.api import Dataset, DatabaseEditor, DatabaseViewer, DATABASE_DATA_FORMAT_NAME
from ....lib.impl.formats.extended import ExtendedViewer, ExtendedEditor, ExtendedFormat
from ..inference_result.api import InferenceResultViewer, InferenceResultEditor, \
    INFERENCE_RESULT_DATA_FORMAT_NAME


class InferenceResultViewerImpl(InferenceResultViewer, ExtendedViewer[DatabaseViewer]):
    @property
    def values(self) -> Dataset:
        return self._parent.datasets.get('preds')


class InferenceResultEditorImpl(InferenceResultEditor, ExtendedEditor[DatabaseEditor]):
    pass


class InferenceResultFormat(ExtendedFormat):
    def __init__(self):
        ExtendedFormat.__init__(self, type_name=INFERENCE_RESULT_DATA_FORMAT_NAME,
                                metadata_type=SIMPLE_METADATA_FORMAT_NAME,
                                base_format=data_formats.get(DATABASE_DATA_FORMAT_NAME),
                                extended_viewer_factory=InferenceResultViewerImpl,
                                extended_editor_factory=InferenceResultEditorImpl)
