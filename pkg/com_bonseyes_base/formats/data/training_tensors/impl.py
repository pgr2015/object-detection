from com_bonseyes_base.formats.metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from ..data_tensors.api import DataTensorsViewer, DataTensorsEditor, \
    DATA_TENSORS_DATA_FORMAT_NAME

from ..composite_directory.api import CompositeViewer, CompositeEditor
from ..composite_directory.format import CompositeFormat
from ....lib.impl.formats.extended import ExtendedFormat, ExtendedViewer, ExtendedEditor
from .api import TrainingTensorsViewer, TrainingTensorsEditor, TRAINING_GROUP_NAME, \
    VALIDATION_GROUP_NAME, TRAINING_TENSORS_DATA_FORMAT_NAME


class TrainingTensorsViewerImpl(TrainingTensorsViewer, ExtendedViewer[CompositeViewer]):

    @property
    def learning_data(self) -> DataTensorsViewer:
        viewer = self.parent.components.get(TRAINING_GROUP_NAME).viewer  # type: DataTensorsViewer
        return viewer

    @property
    def validation_data(self) -> DataTensorsViewer:
        viewer = self.parent.components.get(VALIDATION_GROUP_NAME).viewer  # type: DataTensorsViewer
        return viewer


class TrainingTensorsEditorImpl(TrainingTensorsEditor, ExtendedEditor[CompositeEditor]):

    @property
    def learning_data(self) -> DataTensorsEditor:
        editor = self.parent.components.get(TRAINING_GROUP_NAME).editor  # type: DataTensorsEditor
        return editor

    @property
    def validation_data(self) -> DataTensorsEditor:
        editor = self.parent.components.get(VALIDATION_GROUP_NAME).editor  # type: DataTensorsEditor
        return editor


class TrainingTensorsFormat(ExtendedFormat):
    def __init__(self):
        training_tensor_composite = CompositeFormat(TRAINING_TENSORS_DATA_FORMAT_NAME,
                                                    SIMPLE_METADATA_FORMAT_NAME,
                                                    {TRAINING_GROUP_NAME: DATA_TENSORS_DATA_FORMAT_NAME,
                                                     VALIDATION_GROUP_NAME: DATA_TENSORS_DATA_FORMAT_NAME})

        ExtendedFormat.__init__(self, TRAINING_TENSORS_DATA_FORMAT_NAME,
                                SIMPLE_METADATA_FORMAT_NAME,
                                training_tensor_composite,
                                TrainingTensorsViewerImpl,
                                TrainingTensorsEditorImpl)
