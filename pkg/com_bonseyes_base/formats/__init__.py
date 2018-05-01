from com_bonseyes_base.formats.data.blob.format import BlobDataFormat
from com_bonseyes_base.formats.data.data_tensors.impl import DataTensorsFormat
from com_bonseyes_base.formats.data.database.format import DatabaseFormat
from com_bonseyes_base.formats.data.dataset.format import DataSetFormat
from com_bonseyes_base.formats.data.directory.format import DirectoryDataFormat
from com_bonseyes_base.formats.data.inference_inspect.impl import InferenceInspectFormat
from com_bonseyes_base.formats.data.inference_result.impl import InferenceResultFormat
from com_bonseyes_base.formats.data.training_tensors.impl import TrainingTensorsFormat
from com_bonseyes_base.formats.metadata.simple.format import SimpleMetadataFormat
from com_bonseyes_base.formats.metrics.blob.format import BlobMetricFormat
from com_bonseyes_base.formats.metrics.dataset_processing.format import DatasetProcessingMetricFormat
from com_bonseyes_base.formats.metrics.timeseries.format import TimeSeriesMetricFormat
from com_bonseyes_base.lib.api.data import data_formats
from com_bonseyes_base.lib.api.metadata import metadata_formats
from com_bonseyes_base.lib.api.metrics import metric_formats


def register_all():
    data_formats.register(BlobDataFormat())
    data_formats.register(DataTensorsFormat())
    data_formats.register(DatabaseFormat())
    data_formats.register(DataSetFormat())
    data_formats.register(DirectoryDataFormat())
    data_formats.register(InferenceInspectFormat())
    data_formats.register(InferenceResultFormat())
    data_formats.register(TrainingTensorsFormat())

    metadata_formats.register(SimpleMetadataFormat())

    metric_formats.register(DatasetProcessingMetricFormat())
    metric_formats.register(TimeSeriesMetricFormat())
    metric_formats.register(BlobMetricFormat())
