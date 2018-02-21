import sys

from bonseyes.api import CustomContainerResolver, ProxiedContainerResolver, Container, ArtifactNotFoundException, \
    ArtifactException, Dashboard, Pipeline

from functools import wraps


def catch_artifact_errors(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except ArtifactNotFoundException:
            sys.stderr.write('Not found\n')
            sys.exit(1)
        except ArtifactException as ex:
            sys.stderr.write('Server Error:' + str(ex))
            sys.exit(1)

    return wrapped


def get_artifact_list(args):
    return Container(get_resolver(args).container_url(args.container)).artifacts


def get_resolver(args):

    try:
        container_port = int(args.container)
        return CustomContainerResolver({args.container: 'http://127.0.0.1:%d' % container_port})
    except ValueError:
        pass

    if args.container.startswith('http://'):
        return CustomContainerResolver({args.container: args.container})

    return ProxiedContainerResolver(args.gateway_host, args.gateway_port)


def open_input_files(params):
    input_files = {}

    if params is not None:
        for s in params:
            f = s.split('=')

            if len(f) != 2:
                raise Exception(
                    "File must be specified with name=path/to/file")

            input_files[f[0]] = open(f[1], 'rb')

    return input_files


class ContainersCompleter(object):
    def __call__(self, **kwargs):
        args = kwargs['parsed_args']

        resolver = ProxiedContainerResolver(
            args.gateway_host, args.gateway_port)

        containers = []

        for pipeline in Dashboard(resolver).pipeline_names:
            containers.extend(Pipeline(pipeline, resolver).containers.all())

        return containers


class ArtifactsCompleter(object):
    def __call__(self, **kwargs):
        args = kwargs['parsed_args']
        return get_artifact_list(args).list_all()
