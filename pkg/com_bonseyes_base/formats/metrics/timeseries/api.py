from typing import List

from abc import ABCMeta, abstractmethod

from ....lib.api.metrics import MetricViewer, MetricEditor


TIMESERIES_METRIC_FORMAT_NAME = 'com.bonseyes.metrics.timeseries.0.1'


class Sample:

    def __init__(self, time: float, step: int, value: float):
        self.time = time
        self.step = step
        self.value = value


class TimeSeriesMetricViewer(MetricViewer, metaclass=ABCMeta):

    @abstractmethod
    def samples(self) -> List[Sample]:
        pass


class TimeSeriesMetricEditor(MetricEditor, metaclass=ABCMeta):

    @abstractmethod
    def add_sample(self, time: float, value: float):
        pass
