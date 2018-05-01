import yaml
from ...impl.executor.simple_executor import get_execution

from ...api.workflow import Workflow
from ...cli.commands.run import process_execution
from ...impl.storage.file_storage import FileContext


def retry(args):
    if ':' not in args.execution:
        args.execution = 'local:' + args.execution

    execution = get_execution(args.execution)

    step_index = None
    if args.step is not None:
        step_index = int(args.step)

    update_workflow = None
    if args.workflow is not None:
        with open(args.workflow[0]) as fp:
            data = yaml.load(fp)
        update_workflow = Workflow(data)

    recreate_workers = None
    if args.recreate_worker is not None:
        recreate_workers = [x[0] for x in args.recreate_worker]

    update_context = None
    if args.context is not None:
        update_context = FileContext(args.context[0])

    execution.retry(step_index=step_index, update_workflow=update_workflow, recreate_workers=recreate_workers,
                    update_context=update_context)

    process_execution(execution)


def setup_parser(root_parser, subparsers):
    parser = subparsers.add_parser('retry', help="Retry a previous execution")

    parser.add_argument('execution', help="Execution to retry")
    parser.add_argument('--step', nargs=1, metavar=('STEP_INDEX',), help="Index of step where to restart execution")
    parser.add_argument('--workflow', nargs=1, metavar=('PATH',), help="Update workflow")
    parser.add_argument('--recreate-worker', nargs=1, metavar=('WORKER_NAME',), action="append", help="Update workflow")
    parser.add_argument('--context', nargs=1, metavar=('PATH',), help="Update context")

    parser.set_defaults(func=retry)
