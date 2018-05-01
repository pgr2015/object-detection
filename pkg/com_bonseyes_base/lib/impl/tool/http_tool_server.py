import sys
import traceback
from typing import Dict

from com_bonseyes_base.formats import register_all
from ...api.data import data_formats
from ...api.metadata import metadata_formats
from ...api.metrics import metric_formats
from ..rpc.http_rpc_server import publish_data, publish_method, publish_delete, is_follow_request
from ..utils import follow_file
from ..values.http_values import serve_value
from flask.app import Flask

from ...api.tool import ArtifactStatus
from ..tool.uwsgi_tool import UWSGITool


def trace_exceptions(exception):
    #if isinstance(exception, KeyError):
    #    return 'Not found', 404

    exc_type, exc_value, exc_traceback = sys.exc_info()
    trace = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    return trace, 500, {'Content-Type': 'text/plain'}


def create_app_from_yml():

    tool = UWSGITool()

    # load all the base formats
    register_all()

    # mark all artifact in progress as failed since we are starting up
    tool.cleanup_stale()

    # create the flask app
    app = Flask(__name__, instance_path='/tmp')

    app.register_error_handler(500, trace_exceptions)

    @publish_data(app, '/manifest')
    def publish_manifest():
        return tool.manifest

    @publish_method(app, '/artifacts/')
    def create_artifact(arguments: Dict):

        operation = arguments['operation']

        if operation == 'create':

            command = tool.create_artifact(arguments['artifact_name'],
                                           arguments.get('arguments', {}))

            return {'command_index': command.index}

        else:
            raise Exception("Unsupported operation " + operation)

    @publish_method(app, '/artifacts/<string:artifact_name>/')
    def modify_artifact(artifact_name: str, arguments: Dict):

        operation = arguments['operation']

        if operation == 'modify':
            command = tool.modify_artifact(artifact_name,
                                           arguments['action_name'],
                                           arguments.get('arguments', {}))

            return {'command_index': command.index}

        elif operation == 'wait_for_complete':
            tool.wait_for_completed(artifact_name)

            return {'status': tool.artifacts.get(artifact_name).status}

        else:
            raise Exception("Unsupported operation " + operation)

    @publish_method(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/')
    def modify_command(artifact_name: str, command_index: int, arguments: Dict):

        operation = arguments['operation']

        if operation == 'interrupt':
            tool.interrupt(artifact_name, command_index)

            return {'status': tool.artifacts.get(artifact_name).status}
        else:
            raise Exception("Unsupported operation " + operation)

    @publish_delete(app, '/artifacts/<string:artifact_name>/')
    def delete_artifact(artifact_name: str):
        tool.delete_artifact(artifact_name)

    @publish_data(app, '/artifacts/')
    def get_artifacts():
        return tool.artifacts

    @publish_data(app, '/artifacts/<string:artifact_name>/name')
    def get_artifact_name(artifact_name: str):
        return tool.artifacts.get(artifact_name).name

    @publish_data(app, '/artifacts/<string:artifact_name>/status')
    def get_artifact_status(artifact_name: str):
        return tool.artifacts.get(artifact_name).status

    @publish_data(app, '/artifacts/<string:artifact_name>/history/')
    def get_commands(artifact_name: str):
        return tool.artifacts.get(artifact_name).history

    @publish_data(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/action_name')
    def get_command_action_name(artifact_name: str, command_index: int):
        return tool.artifacts.get(artifact_name).history.get_by_index(command_index).action_name

    @publish_data(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/interrupt_requested')
    def get_command_interrupt_requested(artifact_name: str, command_index: int):
        return tool.artifacts.get(artifact_name).history.get_by_index(command_index).interrupt_requested

    @publish_data(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/log', mimetype='text/plain')
    def get_command_log(artifact_name: str, command_index: int):

        artifact = tool.artifacts.get(artifact_name)

        fp = artifact.history.get_by_index(command_index).open_log()

        changing_log_states = [ArtifactStatus.IN_PROGRESS,
                               ArtifactStatus.PENDING]

        if is_follow_request() and artifact.status in changing_log_states:
            return follow_file(fp, lambda: artifact.status in changing_log_states)

        else:
            return fp

    @publish_data(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/metrics/')
    def get_metrics(artifact_name: str, command_index: int):
        return tool.artifacts.get(artifact_name).history.get_by_index(command_index).metrics

    @publish_data(app, '/artifacts/<string:artifact_name>/data/')
    def get_data_root(artifact_name: str):
        artifact = tool.artifacts.get(artifact_name)
        data_format = data_formats.get(tool.manifest.output_data_format)

        return data_format.get_server().get(artifact.data, '/')

    @publish_data(app, '/artifacts/<string:artifact_name>/data/<path:path>')
    def get_data(artifact_name: str, path: str):
        artifact = tool.artifacts.get(artifact_name)
        data_format = data_formats.get(tool.manifest.output_data_format)

        return data_format.get_server().get(artifact.data, path)

    @publish_data(app, '/artifacts/<string:artifact_name>/metadata/')
    def get_metadata_root(artifact_name: str):
        artifact = tool.artifacts.get(artifact_name)
        data_format = data_formats.get(tool.manifest.output_data_format)
        metadata_format = metadata_formats.get(data_format.metadata_type)

        return metadata_format.get_register_server().get(artifact.metadata, '/')

    @publish_data(app, '/artifacts/<string:artifact_name>/metadata/<path:path>')
    def get_metadata(artifact_name: str, path: str):
        artifact = tool.artifacts.get(artifact_name)
        data_format = data_formats.get(tool.manifest.output_data_format)
        metadata_format = metadata_formats.get(data_format.metadata_type)

        return metadata_format.get_register_server().get(artifact.metadata, path)

    @publish_data(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/metrics/<string:metric_name>/')
    def get_metric_root(artifact_name: str, command_index: int, metric_name: str):
        command = tool.artifacts.get(artifact_name).history.get_by_index(command_index)
        metric = command.metrics.get(metric_name)

        metric_type = tool.manifest.actions.get(command.action_name).metrics.get(metric_name).metric_type
        metric_format = metric_formats.get(metric_type)

        return metric_format.get_server().get(metric, '/')

    @publish_data(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/metrics/<string:metric_name>/<path:path>')
    def get_metric(artifact_name: str, command_index: int, metric_name: str, path: str):
        command = tool.artifacts.get(artifact_name).history.get_by_index(command_index)
        metric = command.metrics.get(metric_name)

        metric_type = tool.manifest.actions.get(command.action_name).metrics.get(metric_name).metric_type
        metric_format = metric_formats.get(metric_type)

        return metric_format.get_server().get(metric, path)

    @publish_data(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/arguments/<string:arg_name>/')
    def get_argument_root(artifact_name: str, command_index: int, arg_name: str):
        command = tool.artifacts.get(artifact_name).history.get_by_index(command_index)
        argument = command.arguments.get(arg_name)

        return serve_value(argument.value, '/')

    @publish_data(app, '/artifacts/<string:artifact_name>/history/<int:command_index>/arguments/<string:arg_name>/<path:path>')
    def get_argument(artifact_name: str, command_index: int, arg_name: str, path: str):
        command = tool.artifacts.get(artifact_name).history.get_by_index(command_index)
        argument = command.arguments.get(arg_name)

        return serve_value(argument.value, path)

    return app
