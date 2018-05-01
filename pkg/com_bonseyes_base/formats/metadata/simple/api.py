from typing import Dict

from abc import ABCMeta, abstractmethod

from ....lib.api.metadata import MetadataViewer, MetadataEditor


SIMPLE_METADATA_FORMAT_NAME = 'com.bonseyes.metadata.simple.0.1'


class SimpleMetadataViewer(MetadataViewer, metaclass=ABCMeta):

    @abstractmethod
    def get(self) -> Dict:
        pass


class SimpleMetadataEditor(MetadataEditor, metaclass=ABCMeta):

    @abstractmethod
    def set(self, data: Dict):
        pass
