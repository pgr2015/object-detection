import json
import sys
from shutil import copyfileobj
from typing import Dict
from uuid import uuid4

import yaml

from com_bonseyes_base.lib.impl.rpc.http_rpc_client import get_stream
from ...impl.executor.simple_executor import get_executor
from ...impl.values.memory_values import ResourceValueFromFile, \
    ResourceValueFromMemory, StringValueFromMemory, PlainObjectValueFromMemory, UrlValueFromMemory

from ...api.executor import ExecutionStatus, SourceDescription, Execution
from ...api.tool import get_tool_from_url
from ...api.values import Value, PlainObjectValue
from ...api.workflow import Workflow
from ...impl.storage.file_storage import FileContext


def add_source_if_missing(sources: Dict[str, SourceDescription], executor: str, execution: str, worker: str) -> str:

    source_name = None

    # try to find an existing source for this output
    for name, source in sources.items():

        if source.execution == execution and \
           source.executor_url == executor and \
           source.worker == worker:
            source_name = name
            break

    # source not found, create a new one with a random name
    if source_name is None:
        source_name = source_name or str(uuid4())
        sources[source_name] = SourceDescription({'executor_url': executor,
                                                  'execution': execution,
                                                  'worker': worker})

    return source_name


def parse_sources_and_params(args):

    # create a list of the sources that we need
    sources = {}  # type: Dict[str, SourceDescription]

    for name, executor, execution, worker in args.source or {}:
        sources[name] = SourceDescription({'executor': executor,
                                           'execution': execution,
                                           'worker': worker})

    # create a list of all the parameters we received and update the sources if necessary
    received_parameters = {}

    for param in args.param or []:

        if len(param) < 3:
            sys.stderr.write('Invalid parameter --param ' + ' '.join(param))
            sys.exit(1)

        name = param[0]

        param_type = param[1]

        # string parameters
        if param_type == 'string':
            received_parameters[name] = StringValueFromMemory(param[2])

        # json parameters
        elif param_type == 'json':

            with open(param[2], 'r') as fp:
                value_data = json.load(fp)

                if not isinstance(value_data, PlainObjectValue):
                    raise ValueError("Invalid value for parameter " + name)

            received_parameters[name] = PlainObjectValueFromMemory(value_data)

        # yaml parameters
        elif param_type == 'yaml':

            with open(param[2], 'r') as fp:
                value_data = yaml.load(fp)

                if not isinstance(value_data, PlainObjectValue):
                    raise ValueError("Invalid value for parameter " + name)

            received_parameters[name] = PlainObjectValueFromMemory(value_data)

        # url parameters
        elif param_type == 'url':
            received_parameters[name] = UrlValueFromMemory(param[2])

        # resource parameters from files
        elif param_type == 'file':
            received_parameters[name] = ResourceValueFromFile(param[2])

        # resources parameters from outputs of previous executions
        elif param_type == 'execution-output':

            if len(param) < 5:
                sys.stderr.write('Invalid parameter --param ' + ' '.join(param))
                sys.exit(1)

            executor = param[2]
            execution = param[3]
            output = param[4]

            output = get_executor(executor).executions.get(execution).outputs.get(output)

            source_name = add_source_if_missing(sources, executor, execution, output.worker_name)

            if output.artifact_name is None:
                url = 'source+http://' + source_name + '/'
            else:
                url = 'source+http://' + source_name + '/artifacts/' + output.artifact_name + '/data/'

            received_parameters[name] = ResourceValueFromMemory(url=url)

        # resource parameters with artifacts from previous executions
        elif param_type == 'execution-artifact':

            if len(param) < 6:
                sys.stderr.write('Invalid parameter --param ' + ' '.join(param))
                sys.exit(1)

            executor = param[2]
            execution = param[3]
            worker = param[4]
            artifact = param[5]

            source_name = add_source_if_missing(sources, executor, execution, worker)

            url = 'source+http://' + source_name + '/artifacts/' + artifact + '/data/'

            received_parameters[name] = ResourceValueFromMemory(url=url)

        # resource parameters with workers from previous executions
        elif param_type == 'execution-worker':

            if len(param) < 5:
                sys.stderr.write('Invalid parameter --param ' + ' '.join(param))
                sys.exit(1)

            executor = param[2]
            execution = param[3]
            worker = param[4]

            source_name = add_source_if_missing(sources, executor, execution, worker)

            url = 'source+http://' + source_name

            received_parameters[name] = ResourceValueFromMemory(url=url)

        else:
            sys.stderr.write('Invalid parameter --param ' + ' '.join(param))
            sys.exit(1)

    return sources, received_parameters


def process_execution(execution: Execution, suspend_at_last_step=False) -> None:
    while True:

        if execution.status == ExecutionStatus.COMPLETED:
            return

        if execution.status == ExecutionStatus.FAILED:
            step_description = execution.current_step.step_description

            worker = execution.workers.get(step_description.worker_name)

            tool = get_tool_from_url(worker.instance.url)

            artifact = tool.artifacts.get(step_description.artifact_name)

            last_command = artifact.history.get_by_index(artifact.history.count - 1)

            print("Error while building artifact:")
            sys.stdout.write(last_command.open_log().read())

            sys.exit(1)

        if execution.status == ExecutionStatus.SUSPENDED:

            if suspend_at_last_step and execution.current_step.index == execution.steps.count - 1:
                return

            else:

                for assignment in execution.current_step.step_description.outputs.all:

                    worker = execution.workers.get(assignment.worker_name)

                    output = execution.workflow.outputs.get(assignment.name)

                    if assignment.artifact_name is None:
                        print(output.label + ": " + worker.instance.url)
                    else:
                        tool = get_tool_from_url(worker.instance.url)
                        artifact = tool.artifacts.get(assignment.artifact_name)
                        print(output.label + ": " + artifact.url)

                input("Execution suspended, press [ENTER] key to continue")

                execution.execute()


def validate_save_params(args):

    if args.save is None:
        return

    for save_option in args.save:

        if save_option[0] == 'worker':
            if len(save_option) < 4:
                sys.stderr.write("Invalid --save worker option")
                sys.exit(1)

        elif save_option[0] == 'output':

            if len(save_option) < 3:
                sys.stderr.write("Invalid --save output option")
                sys.exit(1)

        elif save_option[0] == 'step':

            if len(save_option) < 3:
                sys.stderr.write("Invalid --save step option")
                sys.exit(1)

        else:
            sys.stderr.write("Unsupported save option " + save_option[0])
            sys.exit(1)


def run(root_parser, parser, args):

    validate_save_params(args)

    with open(args.workflow) as fp:
        data = yaml.load(fp)

    if args.save is not None:
        data['steps'].append({'description': "Wait to collect results", 'wait': None})

    workflow = Workflow(data)

    executor = get_executor(args.executor)

    context = FileContext(args.context)

    arguments = {}  # type: Dict[str, Value]

    sources, received_parameters = parse_sources_and_params(args)

    for parameter in workflow.parameters.all:

        if parameter.name not in received_parameters:
            print("Missing parameter " + parameter.name)
            sys.exit(1)

        arguments[parameter.name] = received_parameters[parameter.name].convert_to(parameter.type)

        del received_parameters[parameter.name]

    if len(received_parameters) > 0:
        print("The workflow doesn't have the following parameters:" + str(received_parameters.keys()))
        sys.exit(1)

    if args.config is not None:
        with open(args.config, 'r') as fp:
            config = yaml.load(fp)
    else:
        config = {}

    config_obj = executor.parse_config(config)

    artifact_name = args.name or str(uuid4())

    if args.force:
        try:
            executor.executions.get(artifact_name).delete()
        except KeyError:
            pass

    execution = executor.create_execution(artifact_name, workflow, context, config_obj, arguments, sources)

    execution.execute()

    if args.save is not None:

        process_execution(execution, suspend_at_last_step=True)

        # download all the results
        save_results(args, execution)

        # finish the execution
        execution.execute()
    else:
        process_execution(execution)


def save_results(args, execution):

    for save_option in args.save or []:

        if save_option[0] == 'worker':
            tool = get_tool_from_url(execution.workers.get(save_option[1]).instance.url)

            with open(save_option[3], 'wb') as fpo:
                with tool.artifacts.get(save_option[2]).data.open() as fpi:
                    copyfileobj(fpi, fpo)

        elif save_option[0] == 'output':

            output = execution.outputs.get(save_option[1])

            tool = get_tool_from_url(execution.workers.get(output.worker_name).instance.url)

            with open(save_option[2], 'wb') as fpo:
                with get_stream(tool.artifacts.get(output.artifact_name).data_url) as fpi:
                    copyfileobj(fpi, fpo)

        elif save_option[0] == 'step':

            step = execution.steps.get_by_name(save_option[1])

            tool = get_tool_from_url(execution.workers.get(step.step_description.worker_name).instance.url)

            with open(save_option[2], 'wb') as fpo:
                with get_stream(tool.artifacts.get(step.step_description.artifact_name).data_url) as fpi:
                    copyfileobj(fpi, fpo)

        else:
            sys.stderr.write("Unsupported save option " + save_option[0])

    execution.execute()


def setup_parser(root_parser, subparsers):
    parser = subparsers.add_parser('run', help="Run a workflow")

    parser.add_argument('workflow', help="Workflow to be used")

    parser.add_argument('--executor', default='local:', help="Address of the executor to use")

    parser.add_argument('--name', help="Name of the execution")

    parser.add_argument('--param', nargs='+',
                        action='append', help="Add a parameter. The supported formats are:\n"
                                              "PARAMETER_NAME string STRING\n"
                                              "PARAMETER_NAME url URL\n"
                                              "PARAMETER_NAME json PATH_TO_JSON_FILE\n"
                                              "PARAMETER_NAME yaml PATH_TO_YAML_FILE\n"
                                              "PARAMETER_NAME file PATH_TO_FILE\n"
                                              "PARAMETER_NAME execution-output EXECUTOR_URL "
                                              "EXECUTION_NAME OUTPUT_NAME\n"
                                              "PARAMETER_NAME execution-artifact EXECUTOR_URL "
                                              "EXECUTION_NAME WORKER_NAME ARTIFACT_NAME\n"
                                              "PARAMETER_NAME execution-worker EXECUTOR_URL "
                                              "EXECUTION_NAME WORKER_NAME\n")

    parser.add_argument('--source', nargs=4, metavar=('NAME', 'EXECUTOR', 'EXECUTION', 'WORKER'),
                        action='append', help="Add as source a worker from a previous execution")

    parser.add_argument('--config', help="Execution config")

    parser.add_argument('--force', help="Deletes the artifact if it already exist",
                        action='store_true', default=False)

    parser.add_argument('--wait-completed', help="Waits until the artifact is created",
                        action='store_true', default=False)

    parser.add_argument('--log',
                        help="Show the creation log when completed (works only with"
                             " --wait-completed)",
                        action='store_true', default=False)

    parser.add_argument('--status',
                        help="Show status when the execution is completed",
                        action='store_true', default=False)

    parser.add_argument('--save', nargs='+', action='append',
                        help="Artifacts that need to be collected. It can be:"
                             " - worker worker_name artifact_name output_file to save the "
                             "   artifact artifact_name on worker worker_name to "
                             "   output file output_file "
                             " - step step_name output_file to save the artifact produced "
                             "   in step step_name to output file output_file "
                             " - output output_name output_file to save the output of last step to file output_file)")

    parser.add_argument(
        '--context', default='.', help="Context to be used")

    parser.add_argument(
        '--help-params', action='store_true', help="List the parameters for the workflow")

    parser.set_defaults(func=lambda args: run(root_parser, parser, args))
