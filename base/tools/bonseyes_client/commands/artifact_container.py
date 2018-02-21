#
# NVISO CONFIDENTIAL
#
# Copyright (c) 2017 nViso SA. All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") is the confidential and proprietary information
# owned by nViso or its suppliers or licensors.  Title to the  Material remains
# with nViso SA or its suppliers and licensors. The Material contains trade
# secrets and proprietary and confidential information of nViso or its
# suppliers and licensors. The Material is protected by worldwide copyright and trade
# secret laws and treaty provisions. You shall not disclose such Confidential
# Information and shall use it only in accordance with the terms of the license
# agreement you entered into with nViso.
#
# NVISO MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF
# THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. NVISO SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR
# DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
#


import json
import sys


from bonseyes.api import ArtifactException, ArtifactFailedException, SimpleContainerResolver
from bonseyes.api import Container
from bonseyes_client.utils import open_input_files, get_artifact_list, catch_artifact_errors, get_resolver, \
    ContainersCompleter, ArtifactsCompleter


@catch_artifact_errors
def list_all(args):
    for entity in get_artifact_list(args).list_all():
        print(entity)


@catch_artifact_errors
def status(args):
    print(get_artifact_list(args).get(args.name).get_status())


@catch_artifact_errors
def delete(args):
    get_artifact_list(args).get(args.name).delete()


@catch_artifact_errors
def export(args):
    with open(args.output_file, 'wb') as fp:
        get_artifact_list(args).get(args.name).export(fp, args.path)


@catch_artifact_errors
def log(args):
    get_artifact_list(args).get(args.name).get_log(
        sys.stdout.buffer, follow=args.follow)


@catch_artifact_errors
def input_parameters(args):
    params = get_artifact_list(args).get(args.name).get_input_parameters()
    json.dump(params, sys.stdout, indent=True)
    print()


@catch_artifact_errors
def export(args):
    with open(args.output_file, 'wb') as fp:
        get_artifact_list(args).get(args.name).export(fp, args.path)


@catch_artifact_errors
def list_create_params(args):
    return Container(get_resolver(args).container_url(args.container)).create_params


@catch_artifact_errors
def get_url(args):
    path = Container(get_resolver(args).container_url(
        args.container)).artifact_path
    print(SimpleContainerResolver().container_url(
        args.container) + path + args.name)


@catch_artifact_errors
def create(args):
    try:

        input_files = open_input_files(args.input_file)

        json_data = {}

        if args.parameters:
            json_data = json.loads(args.parameters)

        artifact_list = get_artifact_list(args)

        if args.force:
            try:
                artifact_list.get(args.name).delete()
            except ArtifactException:
                pass

        artifact = artifact_list.create(args.name, json_data, input_files)

        failed = False

        if args.wait_completed or args.log or args.output_file:
            try:
                artifact.wait_for_completed()
            except ArtifactFailedException:
                failed = True

        if args.log:
            artifact.get_log(sys.stdout.buffer)

        if failed:
            sys.exit(1)

        if args.output_file:
            with open(args.output_file, 'wb') as fp:
                artifact.export(fp)

    finally:

        for fp in input_files.values():
            fp.close()


def setup_parser(subparsers):

    parser = subparsers.add_parser(
        'artifact-container', help="Manage container with artifacts")

    p = parser.add_argument('--container', required=True,
                            help="Name of the container where the artifacts reside")
    p.completer = ContainersCompleter()

    subparser = parser.add_subparsers(
        dest='action', help="Action to be performed")
    subparser.required = True

    list_parser = subparser.add_parser(
        'list-artifacts', help="List all artifacts")
    list_parser.set_defaults(func=list_all)

    params_parser = subparser.add_parser('list-create-params', help="List the parameters required to create" +
                                                                    " a new artifact")
    params_parser.set_defaults(func=list_create_params)

    create_parser = subparser.add_parser(
        'create-artifact', help="Create a new artifact")
    create_parser.add_argument('--force', help="Deletes the artifact if it already exist",
                               action='store_true', default=False)
    create_parser.add_argument('--wait-completed', help="Waits until the artifact is created",
                               action='store_true', default=False)
    create_parser.add_argument(
        '--output-file', help="Exports the completed artifact to the specified file")
    create_parser.add_argument('--log', help="Show the creation log when completed (works only with --wait-completed)",
                               action='store_true', default=False)
    create_parser.add_argument(
        '--parameters', help="JSON formatted map with the parameters")
    create_parser.add_argument('--input-file', nargs='*', help="Files that need to be uploaded, " +
                                                               "format is parameter_name=path/to/file")
    create_parser.add_argument('--name', required=True, help="Name of the artifact that will be created " +
                                                             "(must not already exist)")
    create_parser.set_defaults(func=create)

    get_url_parser = subparser.add_parser(
        'artifact-url', help="Return the url of an artifact")
    get_url_parser .add_argument(
        '--name', required=True, help="Name of the artifact to be deleted")
    get_url_parser.set_defaults(func=get_url)

    delete_parser = subparser.add_parser(
        'delete-artifact', help="Delete an existing artifact")
    p = delete_parser.add_argument(
        '--name', required=True, help="Name of the artifact to be deleted")
    p.completer = ArtifactsCompleter()
    delete_parser.set_defaults(func=delete)

    completed_parser = subparser.add_parser(
        'artifact-status', help="Return the current status an artifact")
    p = completed_parser.add_argument(
        '--name', required=True, help="Name of the artifact")
    p.completer = ArtifactsCompleter()
    completed_parser.set_defaults(func=status)

    export_parser = subparser.add_parser(
        'export-artifact', help="Download an artifact")
    p = export_parser.add_argument(
        '--name', required=True, help="Name of the artifact")
    p.completer = ArtifactsCompleter()
    export_parser.add_argument(
        '--path', help="Optional path in the artifact output")
    export_parser.add_argument(
        '--output-file', required=True, help="Path to file that will contain the artifact")
    export_parser.set_defaults(func=export)

    log_parser = subparser.add_parser(
        'artifact-log', help="Download the creation logs for an artifact")
    log_parser.add_argument('--follow', help="Follow the log until the artifact is complete",
                            action='store_true', default=False)
    p = log_parser.add_argument(
        '--name', required=True, help="Name of the artifact")
    p.completer = ArtifactsCompleter()
    log_parser.set_defaults(func=log)

    input_params_parser = subparser.add_parser(
        'artifact-input-params', help="Show the creation parameters of the artifact")
    p = input_params_parser.add_argument(
        '--name', required=True, help="Name of the artifact")
    p.completer = ArtifactsCompleter()
    input_params_parser.set_defaults(func=input_parameters)
