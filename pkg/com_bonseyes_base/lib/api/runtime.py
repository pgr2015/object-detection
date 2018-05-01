from abc import ABCMeta, abstractmethod
from typing import List, Dict, Optional, IO, Union

from .context import Context
from .utils import NamedObject, NamedObjectMap


class InstanceNotRunningException(Exception):
    pass


class UnsupportedInstanceConfigException(Exception):
    pass


class UnsupportedImageConfigException(Exception):
    pass


class InstanceStatus:
    RUNNING = 'running'
    STOPPED = 'stopped'
    MISSING = 'missing'


class Instance(NamedObject, metaclass=ABCMeta):

    @abstractmethod
    def stop(self) -> None:
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        pass

    @abstractmethod
    def delete(self) -> None:
        pass

    @property
    @abstractmethod
    def resources_allocations(self) -> List['ResourceAllocation']:
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @property
    @abstractmethod
    def image(self) -> 'Image':
        pass

    @property
    @abstractmethod
    def cid(self) -> str:
        pass

    @abstractmethod
    def open_log(self) -> IO[str]:
        pass

    @property
    @abstractmethod
    def application(self) -> 'Application':
        pass


class ResourceAllocation(metaclass=ABCMeta):

    @property
    @abstractmethod
    def resource(self) -> 'Resource':
        pass

    @property
    @abstractmethod
    def tool_instance(self) -> Instance:
        pass

    @property
    @abstractmethod
    def quantity(self) -> int:
        pass


class ResourceType:
    GPU = "com.bonseyes.gpu"


class Resource(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def resource_types(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def available(self) -> int:
        pass

    @property
    @abstractmethod
    def total(self) -> int:
        pass


class ImageStatus:
    BUILDING = "building"
    READY = "ready"
    MISSING = "missing"


class PublishConfig:
    pass


class DockerPublishConfig(PublishConfig):
    def __init__(self, registry, name, tag):
        self.registry = registry
        self.name = name
        self.tag = tag


class Image(NamedObject, metaclass=ABCMeta):

    @property
    @abstractmethod
    def status(self) -> str:
        pass

    @abstractmethod
    def delete(self) -> None:
        pass

    @property
    @abstractmethod
    def application(self) -> 'Application':
        pass

    @abstractmethod
    def publish(self, data: PublishConfig) -> None:
        pass

    @abstractmethod
    def open_log(self) -> 'IO[str]':
        pass


class ApplicationConfig(metaclass=ABCMeta):
    pass


class Application(NamedObject, metaclass=ABCMeta):
    """

    An application is a collection of tool images and instances
    that can be used together. It is typically used to instantiate
    all the tools used by a workflow.

    """

    @property
    @abstractmethod
    def images(self) -> NamedObjectMap[Image]:
        pass

    @property
    @abstractmethod
    def instances(self) -> NamedObjectMap[Instance]:
        pass

    @abstractmethod
    def create_image(self, config: 'ImageConfig') -> Image:
        pass

    @abstractmethod
    def create_instance(self, name: str, config: 'InstanceConfig') -> Instance:
        pass

    @abstractmethod
    def delete(self) -> None:
        pass

    @property
    @abstractmethod
    def runtime(self) -> 'Runtime':
        pass

    @property
    @abstractmethod
    def config(self) -> ApplicationConfig:
        pass

    @property
    @abstractmethod
    def context(self) -> Context:
        pass

    @abstractmethod
    def update_context(self, new_context: Context) -> None:
        pass


class Runtime(metaclass=ABCMeta):

    @abstractmethod
    def create_application(self,
                           context: Optional[Context]=None,
                           config: ApplicationConfig=None) -> Application:
        pass

    @property
    @abstractmethod
    def applications(self) -> NamedObjectMap[Application]:
        pass

    @property
    @abstractmethod
    def resources(self) -> NamedObjectMap[Resource]:
        pass

    @property
    @abstractmethod
    def url(self):
        pass

    @abstractmethod
    def parse_application_config(self, data: Dict):
        pass


class ImageConfig:
    pass


class DockerPrebuiltImageConfig(ImageConfig):
    def __init__(self, image_name: str,
                 image_tag: Optional[str]=None,
                 image_registry: Optional[str]=None) -> None:
        self.image_name = image_name
        self.image_tag = image_tag
        self.image_registry = image_registry


class DockerfileImageConfig(ImageConfig):
    def __init__(self, dockerfile: Union[str,List[str]], image_name: str, base_image_data: Optional[Dict]=None) -> None:
        if isinstance (dockerfile,str):
            dockerfile = [dockerfile]

        self.image_name = image_name
        self.dockerfile = dockerfile
        self.base_image_data = base_image_data

    @property
    def base_image(self):

        if self.base_image_data is None:
            return None
        else:
            return get_image_config_from_dict(self.base_image_data)



class ExistingInstanceImageConfig(ImageConfig):
    def __init__(self, application_name: str, instance_name: str) -> None:
        self.application_name = application_name
        self.instance_name = instance_name


class ManifestImageConfig(ImageConfig):
    def __init__(self, manifest_path: str) -> None:
        self.manifest_path = manifest_path


class InstanceConfig:

    @property
    @abstractmethod
    def image_name(self) -> str:
        pass


class DockerFromImageConfig(InstanceConfig):

    def __init__(self, image_name: str, environment: Dict[str, str]=None) -> None:
        self._image_name = image_name
        self._environment = environment

    @property
    def environment(self) -> Dict[str, str]:
        return self._environment

    @property
    def image_name(self) -> str:
        return self._image_name


class DockerFromContainerConfig(InstanceConfig):

    def __init__(self, application_name: str, instance_name: str, image_name: str) -> None:
        self._instance_name = instance_name
        self._application_name = application_name
        self._image_name = image_name

    @property
    def instance_name(self) -> str:
        return self._instance_name

    @property
    def application_name(self) -> str:
        return self._application_name

    @property
    def image_name(self) -> str:
        return self._image_name


def get_image_config_from_dict(data: Dict) -> ImageConfig:

    if 'manifest' in data:
        return ManifestImageConfig(data['manifest'])

    if data.get('image_type') == 'docker-image':
        return DockerPrebuiltImageConfig(data['name'],
                                         data.get('tag'),
                                         data.get('registry'))

    elif data.get('image_type') == 'dockerfile':
        return DockerfileImageConfig(data['dockerfile'],
                                     data['name'],
                                     data.get('base_image'))

    else:
        raise ValueError('Impossible to create config')
