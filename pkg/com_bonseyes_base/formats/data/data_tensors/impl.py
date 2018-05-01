from typing import List, Tuple, Optional

import numpy

from com_bonseyes_base.formats.data.database.format import DatabaseFormat
from com_bonseyes_base.formats.metadata.simple.api import SIMPLE_METADATA_FORMAT_NAME
from .api import DataTensorsEditor, \
    DATA_TENSOR_SAMPLE_NAMES_DATASET_NAME, DATA_TENSOR_CLASS_NAMES_DATASET_NAME, DATA_TENSOR_OUTPUT_DATASET_NAME, \
    DimensionNames, DATA_TENSOR_INPUT_DATASET_NAME, DataTensorsViewer, DATA_TENSORS_DATA_FORMAT_NAME
from ..database.api import Dataset, DataType, DatabaseEditor, DatabaseViewer
from ....lib.impl.formats.extended import ExtendedViewer, ExtendedEditor, ExtendedFormat


class DataTensorsViewerImpl(DataTensorsViewer, ExtendedViewer[DatabaseViewer]):
    @property
    def input_data(self) -> Dataset:
        return self.parent.datasets.get(DATA_TENSOR_INPUT_DATASET_NAME)

    @property
    def output_data(self) -> Dataset:
        return self.parent.datasets.get(DATA_TENSOR_OUTPUT_DATASET_NAME)

    @property
    def class_names(self) -> List[str]:
        return list(self.parent.datasets.get(DATA_TENSOR_CLASS_NAMES_DATASET_NAME)[:].tolist())

    @property
    def sample_names(self) -> List[str]:
        return list(self.parent.datasets.get(DATA_TENSOR_SAMPLE_NAMES_DATASET_NAME)[:].tolist())


class DataTensorsEditorImpl(DataTensorsEditor, ExtendedEditor[DatabaseEditor]):
    def initialize(self, class_count: int,
                   input_dimensions: List[Tuple[str, int]],
                   output_dimensions: List[Tuple[str, int]],
                   input_data_type: str,
                   output_data_type: str):

        self.parent.add_dataset(DATA_TENSOR_SAMPLE_NAMES_DATASET_NAME,
                                shape=(0,), maxshape=(None,),
                                data_type=DataType.STRING,
                                dimension_names=None)

        if class_count is not None:
            self.parent.add_dataset(DATA_TENSOR_CLASS_NAMES_DATASET_NAME,
                                    shape=(class_count,),
                                    data_type=DataType.STRING,
                                    maxshape=None, dimension_names=None)

        input_shape = tuple([x[1] for x in input_dimensions])
        input_names = tuple([x[0] for x in input_dimensions])

        self.parent.add_dataset(DATA_TENSOR_INPUT_DATASET_NAME,
                                shape=(0,) + input_shape,
                                dimension_names=(DimensionNames.SAMPLE,) + input_names,
                                maxshape=(None,) + input_shape,
                                data_type=input_data_type)

        if output_dimensions is not None:
            output_shape = tuple([x[1] for x in output_dimensions])
            output_names = tuple([x[0] for x in output_dimensions])

            self.parent.add_dataset(DATA_TENSOR_OUTPUT_DATASET_NAME,
                                    shape=(0,) + output_shape,
                                    dimension_names=(DimensionNames.SAMPLE,) + output_names,
                                    maxshape=(None,) + output_shape,
                                    data_type=output_data_type)

    def set_class_name(self, class_idx: int, class_name: str) -> None:
        self.parent.datasets.get(DATA_TENSOR_CLASS_NAMES_DATASET_NAME)[class_idx] = class_name

    def append_sample_data(self, names: List[str],
                           input_data: numpy.ndarray,
                           output_data: Optional[numpy.ndarray]):

        database = self.parent

        samples_dataset = database.datasets.get(DATA_TENSOR_SAMPLE_NAMES_DATASET_NAME)
        input_dataset = database.datasets.get(DATA_TENSOR_INPUT_DATASET_NAME)

        previous_samples_count = samples_dataset.dimensions.get_by_index(0).size
        total_samples_count = previous_samples_count + len(names)

        samples_dataset.resize(total_samples_count, 0)
        samples_dataset[previous_samples_count:] = names

        input_dataset.resize(total_samples_count, 0)
        input_dataset[previous_samples_count:] = input_data

        if output_data is not None:
            output_dataset = database.datasets.get(DATA_TENSOR_OUTPUT_DATASET_NAME)
            output_dataset.resize(total_samples_count, 0)
            output_dataset[previous_samples_count:] = output_data


class DataTensorsFormat(ExtendedFormat[DataTensorsViewer, DataTensorsEditor]):
    def __init__(self):
        ExtendedFormat.__init__(self, type_name=DATA_TENSORS_DATA_FORMAT_NAME,
                                metadata_type=SIMPLE_METADATA_FORMAT_NAME,
                                base_format=DatabaseFormat(),
                                extended_viewer_factory=DataTensorsViewerImpl,
                                extended_editor_factory=DataTensorsEditorImpl)
