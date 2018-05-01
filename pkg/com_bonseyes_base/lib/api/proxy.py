from abc import ABCMeta, abstractmethod
import os
import uuid
from typing import TypeVar, Callable, Dict

from .runtime import ManifestImageConfig, DockerFromImageConfig
from .tool import get_tool_from_url, Tool, Artifact
from .values import Value
from ..impl.executor.simple_executor import get_runtime
from ..impl.storage.file_storage import FileContext


class Proxy(metaclass=ABCMeta):
    def __init__(self, tool: Tool):
        self._tool = tool
        self._artifact_cnt = 0

    def _create_artifact(self, arguments: Dict[str, Value]) -> Artifact:
        self._artifact_cnt += 1
        name = "artifact" + str(self._artifact_cnt)
        self._tool.create_artifact(name, arguments)
        self._tool.wait_for_completed(name)
        return self._tool.artifacts.get(name)

    @staticmethod
    @abstractmethod
    def _get_manifest_name() -> str:
        pass

    @property
    def url(self) -> str:
        return self._tool.url

T = TypeVar('T', bound=Proxy)


class App:

    def __init__(self, runtime_name: str = 'local:', verbose: bool = True):
        runtime = get_runtime(runtime_name)
        self._application = runtime.create_application(FileContext("."))
        # Progressive number of tools created
        self.__tool_count = 0
        self.__verbose = verbose

    def create_tool(self, proxy_factory: Callable[[Tool], T], name: str = None, tool_manifest: str = None) -> T:
        """ Create a tool proxy form its manifest """
        if tool_manifest is None:
            tool_manifest = proxy_factory._get_manifest_name()

        if name is None:
            name = 'tool' + str(self.__tool_count)
        self.__tool_count += 1

        image = self._application.create_image(ManifestImageConfig(os.path.join(tool_manifest)))
        instance = self._application.create_instance(name, DockerFromImageConfig(image.name))
        if self.__verbose:
            print("Tool CID: " + str(instance.cid) + " URL: " + instance.url+ " " + name + ":" + proxy_factory.__name__)
        tool = get_tool_from_url(instance.url)
        tool.wait_until_online()
        return proxy_factory(tool)


