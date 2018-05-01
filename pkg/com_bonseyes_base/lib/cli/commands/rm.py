from ...impl.executor.simple_executor import get_execution


def status(args):

    if ':' not in args.execution:
        args.execution = 'local:' + args.execution

    execution = get_execution(args.execution)

    execution.delete()


def setup_parser(root_parser, subparsers):

    parser = subparsers.add_parser('rm', help="Removes an execution")

    parser.add_argument('execution', help="Execution to remove")

    parser.set_defaults(func=status)
