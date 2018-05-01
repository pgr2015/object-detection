from ..utils import format_table
from ...impl.executor.simple_executor import get_executor


def ps(args):

    executor = get_executor(args.executor)

    if args.q:
        for execution in executor.executions.all:
            print(execution.name)

    else:

        headers = ['Name', 'state']

        results = []

        for execution in executor.executions.all:
            results.append([execution.name, execution.status])

        print(format_table(results, headers))


def setup_parser(root_parser, subparsers):

    parser = subparsers.add_parser('ps', help="Print all execution status")

    parser.add_argument('--executor', default='local:', help="Address of the executor to use")
    parser.add_argument('-q', action="store_true", help="Print only the names of the executions")

    parser.set_defaults(func=ps)
