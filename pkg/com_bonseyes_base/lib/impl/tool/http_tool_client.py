import time
from typing import Dict, IO

import requests
from io import TextIOWrapper

from ..values.http_values import HttpArgument

from ...api.data import DataViewer, data_formats
from ...api.metadata import MetadataViewer, metadata_formats
from ...api.metrics import MetricViewer, metric_formats
from ...api.manifest import Manifest
from ...api.tool import Tool, UnavailableToolException, Command, CommandFailedException, \
    ArtifactStatus, Artifact
from ...api.utils import NamedObjectMap, OrderedNamedObjectList
from ...api.values import Value, Argument
from ..rpc.http_rpc_client import get_json, HttpNamedObjectMap, call_method, get_string, delete, \
    HttpOrderedNamedObjectList, get_stream, follow_stream


class HttpTool(Tool):

    def __init__(self, url: str):
        self._url = url.rstrip('/') + '/'

        self._artifacts = HttpNamedObjectMap(self._url + 'artifacts/',
                                             lambda x_url, name: HttpArtifact(self, x_url, name))

    @property
    def url(self):
        return self._url

    @property
    def manifest(self) -> Manifest:
        data = get_json(self.url + 'manifest')
        return Manifest(data)

    @property
    def artifacts(self) -> NamedObjectMap[Artifact]:
        return self._artifacts

    def wait_until_online(self, timeout: int=10):

        success = False

        for retry_id in range(timeout):
            try:

                ret = requests.get(self._url + 'manifest')

                if ret.status_code != 200:
                    raise UnavailableToolException("Error %d while checking tool health" % ret.status_code)

                ret.close()

                success = True

            except requests.exceptions.ConnectionError:
                time.sleep(1)

        if not success:
            raise UnavailableToolException()

    def create_artifact(self, artifact_name: str, arguments: Dict[str, Value]):

        results = call_method(self._url + 'artifacts/',
                              operation='create',
                              artifact_name=artifact_name,
                              arguments=arguments)

        return self.artifacts.get(artifact_name).history.get_by_index(results['command_index'])

    def modify_artifact(self, artifact_name: str, action_name: str, arguments: Dict[str, Value]) -> Command:

        results = call_method(self._url + 'artifacts/' + artifact_name + '/',
                              operation='modify',
                              action_name=action_name,
                              arguments=arguments)

        return self.artifacts.get(artifact_name).history.get_by_index(results['command_index'])

    def wait_for_completed(self, artifact_name: str) -> None:

        while True:

            call_method(self._url + 'artifacts/' + artifact_name + '/',
                        operation='wait_for_complete')

            status = get_string(self._url + 'artifacts/' + artifact_name + '/status')

            if status == ArtifactStatus.COMPLETED:
                return
            elif status == ArtifactStatus.FAILED:
                raise CommandFailedException("Command failed")

            time.sleep(5)

    def interrupt(self, artifact_name: str, command_index: int):

        call_method(self._url + 'artifacts/' + artifact_name + '/history/' + str(command_index) + '/',
                    operation='interrupt')

    def delete_artifact(self, artifact_name: str):
        delete(self._url + 'artifacts/' + artifact_name + '/')


class HttpArtifact(Artifact):

    def __init__(self, tool: Tool, url: str, name: str):
        self._url = url.rstrip('/') + '/'
        self._tool = tool
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def tool(self) -> Tool:
        return self._tool

    @property
    def history(self) -> OrderedNamedObjectList[Command]:
        return HttpOrderedNamedObjectList(self._url + 'history', lambda url, name: HttpCommand(self, url, name))

    @property
    def data(self) -> DataViewer:
        return data_formats.get(self.tool.manifest.output_data_format).get_viewer(self.data_url)

    @property
    def metadata(self) -> MetadataViewer:
        data_format = data_formats.get(self.tool.manifest.output_data_format)
        return metadata_formats.get(data_format.metadata_type).get_viewer(self.metadata_url)

    @property
    def status(self) -> str:
        return get_string(self._url + 'status')

    @property
    def data_url(self) -> str:
        return self._url + 'data'

    @property
    def metadata_url(self) -> str:
        return self._url + 'metadata'

    @property
    def url(self) -> str:
        return self._url


class HttpCommand(Command):

    def __init__(self, artifact: Artifact, url: str, index: int):
        self._url = url.rstrip('/') + '/'
        self._index = index
        self._artifact = artifact

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return None

    @property
    def artifact(self) -> Artifact:
        return self._artifact

    @property
    def action_name(self) -> str:
        return get_string(self._url + 'action_name')

    @property
    def arguments(self) -> NamedObjectMap[Argument]:
        return HttpNamedObjectMap(self._url + 'arguments', HttpArgument)

    def _get_metric(self, url: str, name: str) -> MetricViewer:
        action_desc = self.artifact.tool.manifest.actions.get(self.action_name)
        metric_desc = action_desc.metrics.get(name)

        metric_viewer = metric_formats.get(metric_desc.metric_type).get_viewer(url, name)

        return metric_viewer

    @property
    def metrics(self) -> NamedObjectMap[MetricViewer]:
        return HttpNamedObjectMap(self._url + 'metrics', self._get_metric)

    def open_log(self) -> IO[str]:
        return TextIOWrapper(get_stream(self._url + 'log'))

    def follow_log(self) -> IO[str]:
        return TextIOWrapper(follow_stream(self._url + 'log'))

    @property
    def interrupt_requested(self) -> bool:
        return bool(get_string(self._url + 'interrupt_requested'))
