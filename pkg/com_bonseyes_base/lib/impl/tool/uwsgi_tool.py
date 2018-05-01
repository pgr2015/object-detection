import importlib
import logging
import sys

import os
import uwsgi
import uwsgidecorators
import yaml
from ..tool.simple_tool import SimpleTool, SimpleToolConfig
from uwsgidecorators import mulefunc

from ...api.manifest import Manifest
from ...api.tool import ArtifactStatus
from ..storage.file_storage import FileStorage


class UWSGIToolConfig(SimpleToolConfig):

    @property
    def data_dir(self):
        return self._data.get('data_dir', '/data')

    @property
    def manifest_path(self):
        return self._data.get('manifest_path', '/app/manifest.yml')


class UWSGITool(SimpleTool):

    def __init__(self, config_file: str='/app/config.yml'):

        self._config_file = config_file

        if os.path.exists(config_file):
            with open(config_file) as fp:
                data = yaml.load(fp)
        else:
            data = {}

        # loads the setup module to allow the tool to perform some initializations
        if os.path.exists('/app/setup.py'):
            importlib.import_module('setup')

        config = UWSGIToolConfig(data)

        self._uwsgi_config = config

        if not os.path.exists(config.manifest_path):
            raise Exception("Cannot load manifest from " + config.manifest_path)

        with open(config.manifest_path) as fp:
            data = yaml.load(fp)

        manifest = Manifest(data)

        storage = FileStorage(self._uwsgi_config.data_dir)
        SimpleTool.__init__(self, storage, manifest, self._uwsgi_config)

    @property
    def storage(self):
        return self._storage

    def _schedule_execution(self, artifact_name: str):
        schedule_command(self._config_file, artifact_name)

    def cleanup_stale(self):
        for artifact in self.artifacts.all:

            try:
                if artifact.status == ArtifactStatus.IN_PROGRESS:
                    artifact.set_status(ArtifactStatus.FAILED)

            except FileNotFoundError:
                logging.error("Found corrupted artifact " + artifact.name + ", deleting")
                self.delete_artifact(artifact.name)


@uwsgidecorators.postfork
def setup():
    setup_logging()
    attach_debugger()


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    if uwsgi.worker_id() != 0:
        format_prefix = "[pid: %d|worker: %d]" % (
            os.getpid(), uwsgi.worker_id())
    elif uwsgi.mule_id() != 0:
        format_prefix = "[pid: %d|mule: %d]" % (os.getpid(), uwsgi.mule_id())
    else:
        format_prefix = "[pid: %d|other]" % os.getpid()

    formatter = logging.Formatter(
        format_prefix + ' %(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def attach_debugger():
    # attach to the debugger if it is specified
    if 'PYDEVD_DEBUGGER' in os.environ:
        import pydevd
        host, port = os.environ['PYDEVD_DEBUGGER'].split(':')
        pydevd.settrace(host=host, port=int(port), suspend=False)
        import pydevd_file_utils

        for client_path, server_path in pydevd_file_utils.PATHS_FROM_ECLIPSE_TO_PYTHON:
            logging.info("Source %s mapped to %s" % (client_path, server_path))

@mulefunc
def schedule_command(config_file: str, artifact_name: str):

    UWSGITool(config_file).execute_action(artifact_name)

    # exit the mule process to make sure we clean up any allocated resource
    sys.exit(0)
