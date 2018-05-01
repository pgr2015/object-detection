import copy
import os

from typing import Dict, List, Optional, Any, IO

import docker
import logging

import yaml
from docker.client import DockerClient
from docker.errors import ImageNotFound
from docker.models.containers import Container

from com_bonseyes_base.lib.impl.utils import GeneratorReader
from ...api.context import Context, StoredContext
from ...api.manifest import Manifest
from ...api.runtime import Runtime, Instance, InstanceConfig, Application, ImageConfig, Image, \
    DockerPrebuiltImageConfig, DockerfileImageConfig, UnsupportedInstanceConfigException, DockerFromImageConfig, \
    DockerFromContainerConfig, InstanceStatus, ResourceAllocation, InstanceNotRunningException, \
    ExistingInstanceImageConfig, ApplicationConfig, ImageStatus, ManifestImageConfig, \
    PublishConfig, DockerPublishConfig, Resource
from ...api.storage import Storage, StoredNamedObject, StoredNamedObjectMap, StorableObject, StoredStringField, \
    StoredObjectField
from ...api.utils import NamedObjectMap, NamedDataView, create_data_views_from_dict


class ContainerNotFoundException(Exception):
    pass


class SimpleCredential(NamedDataView):

    @property
    def username(self) -> str:
        return self._data.get('user')

    @property
    def password(self) -> str:
        return self._data.get('password')

    @property
    def registry(self) -> str:
        return self.name


class SimpleApplicationConfig(ApplicationConfig, StorableObject):

    def __init__(self, data: Dict):
        self._data = data

    @property
    def build_args(self) -> Dict[str, str]:
        return self._data.get('build_args', {})

    @property
    def docker_timeout(self) -> int:
        return int(self._data.get('docker_timeout', 60))

    @property
    def run_opts(self) -> Dict:
        return self._data.get('run_opts', {})

    @property
    def credentials(self) -> NamedObjectMap[SimpleCredential]:
        return create_data_views_from_dict(self._data.get('credentials', {}), SimpleCredential)

    @property
    def default_pull_registry(self):
        return self._data.get('default_pull_registry')

    @property
    def default_tag(self):
        return self._data.get('default_tag')

    def to_dict(self):
        return self._data


class SimpleInstance(Instance, StoredNamedObject):

    def __init__(self, application: 'SimpleApplication', storage: Storage) -> None:
        StoredNamedObject.__init__(self, storage)
        self._application = application

        self._image_name = StoredStringField(storage, 'image_name', required=True)
        self._cid = StoredStringField(storage, 'cid', required=False)
        self._docker_volume = StoredStringField(storage, 'docker_volume', required=True)

    @property
    def cid(self) -> str:
        return self._cid.get()

    def open_log(self) -> IO[str]:
        return GeneratorReader(self._get_container().logs(stream=True, follow=False))

    def _get_container(self) -> Container:

        cid = self._cid.get()

        if cid is None:
            raise ContainerNotFoundException('No container for this instance')

        containers = self._application.engine.containers.list(all=True, filters={'id': cid})

        if len(containers) == 0:
            raise ContainerNotFoundException('Container ' + cid + ' disappeared')

        return containers[0]

    def stop(self) -> None:
        self._get_container().stop()

    def delete(self) -> None:

        try:
            self._get_container().remove(v=True, force=True)
        except ContainerNotFoundException:
            logging.info("instance " + self.name + ": The container disappeared from docker")
            pass

        self._storage.delete('/')

    def _create_from_image(self, config: DockerFromImageConfig) -> None:

        logging.info("instance " + self.name + ": Creating instance from image")

        engine = self._application.engine

        run_opts = self._application.create_default_run_opts()

        run_opts['image'] = self._application.images.get(config.image_name).docker_image_name

        volume = engine.volumes.create()
        volume_id = volume.id

        if config.environment is not None:
            run_opts['environment'].update(config.environment)

        run_opts['volumes'][volume_id] = {'bind': '/data', 'mode': 'rw'}

        container = engine.containers.run(**run_opts)

        self._cid.set(container.id)
        self._docker_volume.set(volume_id)
        self._image_name.set(config.image_name)

    def _create_from_container(self, config: DockerFromContainerConfig) -> None:

        logging.info("instance " + self.name + ": Creating instance from existing instance")

        engine = self._application.engine

        run_opts = self._application.create_default_run_opts()

        run_opts['image'] = self._application.images.get(config.image_name).docker_image_name

        base_app = self._application.runtime.applications.get(config.application_name)

        base_instance = base_app.instances.get(config.instance_name)

        volume_id = base_instance._docker_volume.get()

        run_opts['volumes'][volume_id] = {'bind': '/data', 'mode': 'ro'}

        container = engine.containers.run(**run_opts)

        self._cid.set(container.id)
        self._docker_volume.set(volume_id)
        self._image_name.set(config.image_name)

    def create(self, config: InstanceConfig) -> None:

        if isinstance(config, DockerFromImageConfig):
            self._create_from_image(config)

        elif isinstance(config, DockerFromContainerConfig):
            self._create_from_container(config)

        else:
            raise UnsupportedInstanceConfigException()

    @property
    def status(self) -> str:
        try:

            container = self._get_container()

            if container.status == 'running':
                return InstanceStatus.RUNNING
            else:
                return InstanceStatus.STOPPED

        except ContainerNotFoundException:
            return InstanceStatus.MISSING

    @property
    def resources_allocations(self) -> List[ResourceAllocation]:
        return []

    @property
    def url(self) -> str:

        if self.status != InstanceStatus.RUNNING:
            raise InstanceNotRunningException()

        container = self._get_container()

        port = self._application.engine.api.port(container.id, 80)[0]['HostPort']

        return 'http://%s:%s' % (self._application.runtime.config.docker_ip, port)

    @property
    def docker_image(self) -> str:
        return self._get_container().image

    @property
    def image(self) -> 'SimpleImage':
        return self._application.images.get(self._image_name.get())

    @property
    def application(self) -> Application:
        return self._application


class SimpleRuntimeConfig(StorableObject):
    def __init__(self, data: Dict) -> None:
        self._data = data

    @property
    def docker_timeout(self) -> int:
        return self._data.get('docker_timeout', 60)

    @property
    def autoclean_images(self) -> bool:
        return self._data.get('autoclean_images', False)

    @property
    def docker_registry_credentials(self) -> Dict[str, Dict[str, str]]:
        return self._data.get('docker_registry_credentials', {})

    @property
    def docker_ip(self) -> str:

        ip = self._data.get('docker_ip')

        if ip is None:

            if 'BE_DOCKER_IP_ADDRESS' in os.environ:
                return os.environ['BE_DOCKER_IP_ADDRESS']
            else:
                # try to autodetect IP
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                finally:
                    s.close()

        return ip

    @property
    def docker_build_args(self) -> Dict[str, str]:
        return copy.deepcopy(self._data.get('docker_build_args', {}))

    @property
    def docker_run_args(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data.get('docker_run_args', {}))

    def to_dict(self):
        return self._data


class SimpleResource(StoredNamedObject, Resource):

    @property
    def resource_types(self) -> List[str]:
        return []

    @property
    def available(self) -> int:
        return 0

    @property
    def total(self) -> int:
        return 0


class GPUResource(StoredNamedObject, Resource):
    pass


class SimpleImage(StoredNamedObject, Image):
    def __init__(self, application: 'SimpleApplication', storage: Storage) -> None:
        StoredNamedObject.__init__(self, storage)

        self._storage = storage
        self._application = application

        self._status = StoredStringField(storage, 'status', required=True)

    @property
    def status(self) -> str:
        return self._status.get()

    @property
    def docker_image_name(self):
        return self.name + ":" + self.application.name

    def create(self, config: ImageConfig):

        self._status.set(ImageStatus.BUILDING)

        engine = self._application.engine
        logging.info('image ' + self.name + ': Creating image')

        # parse the manifest if the config is a manifest config
        if isinstance(config, ManifestImageConfig):

            with self._application.context.get_entry(config.manifest_path).open() as fp:
                data = yaml.load(fp)

            manifest = Manifest(data)

            config = manifest.image_config

        # now that we have the real config we can start creating the image
        if isinstance(config, DockerPrebuiltImageConfig):

            image_name = config.image_name

            registry = None

            if config.image_registry is not None:
                registry = config.image_registry
            elif self._application.config.default_pull_registry is not None:
                registry = self._application.config.default_pull_registry

            if registry is not None:
                if isinstance(registry, str):       # handle the case registry is set to False (use local image) or
                                                    # True (pull from dockerhub official images)
                    image_name = registry + '/' + image_name

            image_tag = None

            if config.image_tag is not None:
                image_tag = config.image_tag
            elif self._application.config.default_tag is not None:
                image_tag = self._application.config.default_tag

            if registry is not None and registry is not False:
                logging.info('image ' + self.name + ': Pulling image from ' + image_name)
                self._application.login_to_registries()
                engine.images.pull(image_name, tag=image_tag)

            if image_tag is not None:
                full_image_name = image_name + ':' + image_tag
            else:
                full_image_name = image_name

            logging.info('image ' + self.name + ': Tagging image ' + image_name)
            engine.api.tag(full_image_name, repository=self.name, tag=self.application.name)

        elif isinstance(config, DockerfileImageConfig):

            with self.application.context.storage.edit('/') as context_path:

                self._application.login_to_registries()

                build_args = self.application.create_default_buildargs()

                # build base image:
                if config.base_image:
                    logging.info('image ' + self.name + ': Creating base image')
                    subimage = self.application.create_image(config.base_image)

                    # pass the image hash exploit cached builds
                    image_id = engine.images.get(subimage.docker_image_name).id
                    build_args['BASE_IMAGE'] = image_id

                    logging.info('image ' + self.name + ': Created base image ' + subimage.name)

                # build the image itself

                # logging.info('image ' + self.name + ': Building image')

                with self.storage.open('log', 'w') as fp:
                    base_count = len(config.dockerfile)
                    for i, dockerfile in enumerate(config.dockerfile):
                        image_id = self.docker_image_name
                        if i < base_count - 1:
                            # don't add extension to last image so that it has the correct name
                            image_id += "." + str(i)
                        ret = engine.api.build(path=context_path,
                                               dockerfile=dockerfile,
                                               buildargs=build_args,
                                               tag=image_id,
                                               rm=True, decode=True)

                        # Use this image as base for the next one
                        build_args['BASE_IMAGE'] = image_id

                        # Append build log
                        for data in ret:
                            if 'stream' in data:
                                fp.write(data['stream'])
                                fp.flush()
                            elif 'errorDetail' in data:
                                with self.open_log() as fp:
                                    log_info = fp.read()
                                raise Exception("image " + self.name + ": Error while building:\n "
                                                + str(data['errorDetail']) + "\n" + log_info)

                # logging.info('image ' + self.name + ': Building image completed')

        elif isinstance(config, ExistingInstanceImageConfig):

            app = self.application.runtime.applications.get(config.application_name)
            instance = app.instances.get(config.instance_name)

            logging.info('image ' + self.name + ': Tagging existing image ' + instance.image.docker_image_name)
            engine.api.tag(instance.image.docker_image_name,
                           repository=self.name,
                           tag=self.application.name)

        else:
            self._status.set(ImageStatus.MISSING)
            raise Exception("Unsupported type of image config " + str(type(config)))

        self._status.set(ImageStatus.READY)

    def delete(self) -> None:

        if self.status == ImageStatus.READY:

            if self.application.runtime.config.autoclean_images:
                try:
                    self._application.engine.images.remove(self.docker_image_name)
                except ImageNotFound:
                    logging.info("image " + self.name + ": The image disappeared from docker")

        self._storage.delete('/')

    def open_log(self) -> 'IO[str]':
        return self._storage.open('log', 'r')


    @property
    def application(self) -> 'SimpleApplication':
        return self._application

    def publish(self, config: PublishConfig) -> None:

        if not isinstance(config, DockerPublishConfig):
            raise ValueError("Cannot publish with config " + str(type(config)))

        if config.registry:

            self._application.login_to_registries()

            self._application.engine.api.tag(self.docker_image_name,
                                             config.registry + '/' + config.name, tag=config.tag)

            self._application.engine.api.push(config.registry + '/' + config.name + ':' + config.tag)

        else:

            self._application.engine.api.tag(self.docker_image_name, config.name, tag=config.tag)


class SimpleApplication(StoredNamedObject, Application):

    def __init__(self, runtime: 'SimpleRuntime', storage: Storage) -> None:
        StoredNamedObject.__init__(self, storage)

        self._engine = None  # type: Optional[DockerClient]

        self._storage = storage
        self._runtime = runtime

        self._instances = StoredNamedObjectMap(self._storage.get_substorage('/instances'),
                                               lambda x: SimpleInstance(self, x))

        self._images = StoredNamedObjectMap(self._storage.get_substorage('/images'),
                                            lambda x: SimpleImage(self, x))

        self._config = StoredObjectField(storage, 'config', SimpleApplicationConfig, required=True)

    def create_instance(self, name: str, config: InstanceConfig) -> SimpleInstance:

        instances_substorage = self._storage.get_substorage('instances')
        instance = SimpleInstance(self, instances_substorage.get_substorage(name))
        instance.create(config)

        return instance

    def create_image(self, config: ImageConfig) -> SimpleImage:

        image_substorage = self._storage.get_substorage('images')
        image = SimpleImage(self, image_substorage.create_new_substorage())
        image.create(config)

        return image

    @property
    def context(self) -> StoredContext:
        return StoredContext(self._storage.get_substorage('/context'))

    def update_context(self, new_context: Context) -> None:

        # delete old context
        context_storage = self._storage.get_substorage('context')
        context_storage.delete('/')

        # save the new context
        context_storage = self._storage.get_substorage('context')
        new_context.save_to_storage(context_storage)

    @property
    def instances(self) -> NamedObjectMap[SimpleInstance]:
        return self._instances

    @property
    def images(self) -> NamedObjectMap[SimpleImage]:
        return self._images

    @property
    def runtime(self) -> 'SimpleRuntime':
        return self._runtime

    @property
    def config(self) -> SimpleApplicationConfig:
        return self._config.get()

    def create(self, context: Optional[Context]=None, config: ApplicationConfig=None) -> None:
        context_storage = self._storage.get_substorage('context')

        if context is not None:
            context.save_to_storage(context_storage)

        if config is None:
            config = SimpleApplicationConfig({})

        if not isinstance(config, SimpleApplicationConfig):
            raise ValueError("Invalid config type " + str(type(config)))

        self._config.set(config)

    def delete(self):
        for instance in self.instances.all:
            instance.delete()

        for image in self.images.all:
            image.delete()

        self._storage.delete('/')

    @property
    def engine(self) -> DockerClient:
        if self._engine is None:
            self._engine = docker.from_env(timeout=self.config.docker_timeout)

        return self._engine

    def create_default_run_opts(self) -> Dict:

        run_args = self.runtime.config.docker_run_args
        run_args.update(self.config.run_opts)
        run_args.update({'detach': True, 'ports': {'80/tcp': None}})

        if 'volumes' not in run_args:
            run_args['volumes'] = {}

        if 'environment' not in run_args:
            run_args['environment'] = {}

        return run_args

    def create_default_buildargs(self) -> Dict:

        build_args = self.runtime.config.docker_build_args
        build_args.update(self.config.build_args)

        return copy.deepcopy(self.config.build_args)

    def login_to_registries(self) -> None:

        for credentials in self.config.credentials.all:

            self._engine.login(username=credentials.username,
                               password=credentials.password,
                               registry=credentials.registry)


class SimpleRuntime(Runtime):

    def __init__(self, storage: Storage) -> None:
        self._storage = storage

        self._resources = StoredNamedObjectMap(self._storage.get_substorage('/resources'), SimpleResource)
        self._applications = StoredNamedObjectMap(self._storage.get_substorage('/applications'),
                                                  lambda x: SimpleApplication(self, x))

        self._config = StoredObjectField(storage, 'config', SimpleRuntimeConfig, required=False)

    def create_application(self, context: Optional[Context]=None, environment: Dict=None) -> SimpleApplication:
        instances_substorage = self._storage.get_substorage('applications')
        application = SimpleApplication(self, instances_substorage.create_new_substorage())

        application.create(context, environment)

        return application

    @property
    def config(self) -> SimpleRuntimeConfig:
        return self._config.get(SimpleRuntimeConfig({}))

    @property
    def resources(self) -> NamedObjectMap[Resource]:
        return self._resources

    @property
    def url(self):
        return "local:"

    @property
    def applications(self) -> NamedObjectMap[SimpleApplication]:
        return self._applications

    def parse_application_config(self, data: Dict):
        return SimpleApplicationConfig(data)
