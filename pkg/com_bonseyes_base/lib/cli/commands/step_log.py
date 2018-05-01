import sys

from ...api.runtime import InstanceStatus
from ...api.tool import get_tool_from_url
from ...impl.executor.simple_executor import get_executor


def status(args):

    executor = get_executor(args.executor)

    execution = executor.executions.get(args.execution)

    try:
        step = execution.steps.get_by_name(args.step)

    except KeyError:
        step = execution.steps.get_by_index(int(args.step))

    if step.step_description.is_wait:
        sys.stderr.write("Cannot get log of a wait step\n")
        sys.exit(1)

    worker = execution.workers.get(step.step_description.worker_name)

    if worker.instance.status != InstanceStatus.RUNNING:
        sys.stderr.write("Cannot get log because the worker is not running\n")
        sys.exit(1)

    tool = get_tool_from_url(worker.instance.url)

    artifact = tool.artifacts.get(step.step_description.artifact_name)

    last_command = artifact.history.get_by_index(artifact.history.count - 1)

    if args.follow:
        # FIXME: follow
        raise Exception("Not implemented")

    sys.stdout.write(last_command.open_log().read())


def setup_parser(root_parser, subparsers):

    parser = subparsers.add_parser('step-log', help="Print log of a step")

    parser.add_argument('--executor', default="local:", help="Execution to display")

    parser.add_argument('execution', help="Execution to display")
    parser.add_argument('step', help="Step index or name to display")

    parser.add_argument('--follow', help="Continue displaying the log until the step finishes")

    parser.set_defaults(func=status)
