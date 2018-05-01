import sys
from shutil import copyfileobj
from typing import Dict
from typing import List
from typing import Tuple
from uuid import uuid4

import yaml

from com_bonseyes_base.lib.api.context import MemoryContext
from com_bonseyes_base.lib.impl.rpc.http_rpc_client import get_stream
from ...impl.executor.simple_executor import get_executor

from ...api.executor import ExecutionStatus, SourceDescription
from ...api.tool import get_tool_from_url
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


def save(args):

    data = {'description': 'Save artifacts',
            'steps': [{'description': "Wait to collect results", 'wait': None}]}

    workflow = Workflow(data)

    executor = get_executor(args.executor)

    if args.config is not None:
        with open(args.config, 'r') as fp:
            config = yaml.load(fp)
    else:
        config = {}

    config_obj = executor.parse_config(config)

    # create a list of the sources that we need
    sources = {}  # type: Dict[str, SourceDescription]

    to_collect = []  # type: List[Tuple[str, str, str]]

    for output_name, output_file in args.output or []:
        output = get_executor(args.executor).executions.get(args.execution).outputs.get(output_name)
        source_name = add_source_if_missing(sources, args.executor, args.execution, output.worker_name)
        to_collect.append((source_name, output.artifact_name, output_file))

    for worker_name, artifact_name, output_file in args.artifact or []:
        source_name = add_source_if_missing(sources, args.executor, args.execution, worker_name)
        to_collect.append((source_name, artifact_name, output_file))

    for step_name, output_file in args.step or []:
        step = get_executor(args.executor).executions.get(args.execution).steps.get_by_name(step_name)
        source_name = add_source_if_missing(sources, args.executor, args.execution, step.step_description.worker_name)
        to_collect.append((source_name, step.step_description.artifact_name, output_file))

    execution = executor.create_execution(str(uuid4()), workflow, MemoryContext(), config_obj, {}, sources)

    try:

        execution.execute()

        if execution.status != ExecutionStatus.SUSPENDED:
            sys.stderr.write("Error while loading data")
            return

        # collect all artifacts from sources
        for source_name, artifact_name, output_file in to_collect:

            tool = get_tool_from_url(execution.sources.get(source_name).instance.url)

            with open(output_file, 'wb') as fpo:
                with get_stream(tool.artifacts.get(artifact_name).data_url) as fpi:
                    copyfileobj(fpi, fpo)

        execution.execute()

    finally:

        execution.delete()


def setup_parser(root_parser, subparsers):
    parser = subparsers.add_parser('save', help="Save artifacts of a workflow")

    parser.add_argument('execution', help="Execution containing the artifact to save")

    parser.add_argument('--executor', default='local:', help="Address of the executor to use")

    parser.add_argument('--config', help="Execution config")

    parser.add_argument('--artifact', nargs=3, metavar=["WORKER_NAME", "ARTIFACT_NAME", "OUTPUT_FILE"], action='append',
                        help="Save the artifact ARTIFACT_NAME on worker WORKER_NAME to output file OUTPUT_FILE")

    parser.add_argument('--step', nargs=2, metavar=["STEP_NAME", "OUTPUT_FILE"], action='append',
                        help="Save the artifact produced by step with name STEP_NAME to output file OUTPUT_FILE")

    parser.add_argument('--output', nargs=2, metavar=["OUTPUT_NAME", "OUTPUT_FILE"], action='append',
                        help="Save the output with name OUTPUT_NAME to output file OUTPUT_FILE")

    parser.set_defaults(func=save)
