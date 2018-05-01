import json
import sys

import yaml
from ...impl.executor.simple_executor import get_runtime

from ...api.manifest import Manifest
from ...api.runtime import DockerPublishConfig, DockerfileImageConfig
from ...impl.storage.file_storage import FileContext


def build(args):

    runtime = get_runtime(args.runtime)

    config = None

    if args.config is not None:

        with open(args.config) as fp:
            data = json.load(fp)

        config = runtime.parse_application_config(data.get("application_config", {}))

    with open(args.manifest) as fp:
        data = yaml.load(fp)

    manifest = Manifest(data)

    image_config = manifest.image_config

    if not isinstance(image_config, DockerfileImageConfig):
        print("Cannot build image that is not of dockerfile type")
        sys.exit(1)

    application = runtime.create_application(FileContext(args.context), config)

    try:

        image = application.create_image(image_config)

        if args.publish is not None:
            image.publish(DockerPublishConfig(*args.publish))

        if args.tag is not None:

            image.publish(DockerPublishConfig(registry=False,
                                              name=image_config.image_name,
                                              tag=args.tag))

    except:

        application.delete()

        raise


def setup_parser(root_parser, subparsers):

    parser = subparsers.add_parser('build', help="Build an image from a manifest")

    parser.add_argument('manifest', help="Manifest to build")

    parser.add_argument('--runtime', default="local:", help="URL of the runtime to use")
    parser.add_argument('--context', default=".", help="Context to use for the build")
    parser.add_argument('--config', help="Runtime config")
    parser.add_argument('--publish', metavar=('REPOSITORY', 'NAME', 'TAG'),
                        nargs=3, help="Push the resulting image to a repository")

    parser.add_argument('--tag', metavar='TAG',
                        nargs=1, help="Tag the image on the local repository")

    parser.set_defaults(func=build)
