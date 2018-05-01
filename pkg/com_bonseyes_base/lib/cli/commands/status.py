from ...api.executor import Execution, SourceStatus
from ...api.runtime import InstanceStatus
from ...cli.utils import format_table
from ...impl.executor.simple_executor import get_executor


def print_workers(execution: Execution):
    print("Workers")
    print("============")
    print()

    headers = ['Name', 'State', 'URL', 'CID']

    results = []

    for worker in execution.workers.all:

        if worker.status == SourceStatus.CREATED:
            if worker.instance.status == InstanceStatus.RUNNING:
                url = worker.instance.url
            else:
                url = 'N/A'
            cid = worker.instance.cid[0:10]
        else:
            url = 'N/A'
            cid = 'N/A'

        results.append([worker.name, worker.status, url, cid])

    print(format_table(results, headers))
    print()


def print_sources(execution: Execution):
    print("Sources")
    print("============")
    print()

    if execution.sources.count == 0:
        print("None")
        print()
        return

    headers = ['Name', 'State', 'URL', 'CID']

    results = []

    for source in execution.sources.all:

        if source.status == SourceStatus.CREATED:
            url = source.instance.url
            cid = source.instance.cid[0:10]
        else:
            url = 'N/A'
            cid = 'N/A'

        results.append([source.name, source.status, url, cid])

    print(format_table(results, headers))
    print()


def print_steps(execution: Execution):
    print("Steps")
    print("============")
    print()

    headers = ['Index', 'Name', 'Description', 'Status']

    results = []

    for step in execution.steps.all:
        results.append([str(step.index), step.name or "N/A", step.step_description.description, step.status])

    print(format_table(results, headers))
    print()


def status(args):

    executor = get_executor(args.executor)

    execution = executor.executions.get(args.execution)

    print_workers(execution)
    print_sources(execution)
    print_steps(execution)


def setup_parser(root_parser, subparsers):

    parser = subparsers.add_parser('status', help="Print status of an execution")

    parser.add_argument('--executor', default="local:", help="Execution to display")

    parser.add_argument('execution', help="Execution to display")

    parser.set_defaults(func=status)
