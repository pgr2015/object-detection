from typing import Optional

from abc import ABCMeta, abstractmethod

from ....lib.api.metrics import MetricViewer, MetricEditor


DATA_PROCESSING_METRIC_FORMAT_NAME = 'com.bonseyes.metrics.dataset-processing.0.1'


class DatasetProcessingMetricViewer(MetricViewer, metaclass=ABCMeta):

    @property
    @abstractmethod
    def processed_samples(self) -> int:
        pass

    @property
    @abstractmethod
    def remaining_samples(self) -> Optional[int]:
        pass


class DatasetProcessingMetricEditor(MetricEditor, metaclass=ABCMeta):

    @abstractmethod
    def set_processed_samples(self, processed_samples: int) -> None:
        pass

    @abstractmethod
    def set_remaining_samples(self, remaining_samples: int) -> None:
        pass
