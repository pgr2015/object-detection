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

from bonseyes.api import Dashboard

from bonseyes_client.utils import get_resolver, get_artifact_list, catch_artifact_errors


def _list_all_artifacts(args):
    artifacts = []

    for container in Dashboard(get_resolver(args)).containers:
        artifacts += [container + ':' +
                      x for x in get_artifact_list(args, container).list_all()]

    return artifacts


class ArtifactsCompleter(object):
    def __call__(**kwargs):
        args = kwargs['parsed_args']

        return _list_all_artifacts(args)


def _get_artifact(name, args):

    if name is None:
        sys.stderr.write("You must specify an artifact name\n")
        sys.exit(1)

    container, artifact_name = name.split(':', 1)

    return get_artifact_list(args, container).get(artifact_name)



@catch_artifact_errors
def list_all(args):

    for artifact in _list_all_artifacts(args):
        print(artifact)


@catch_artifact_errors
def status(args):
    print(_get_artifact(args.name, args).get_status())


@catch_artifact_errors
def delete(args):
    for name in args.names:
        _get_artifact(name, args).delete()


@catch_artifact_errors
def export(args):
    with open(args.output_file, 'wb') as fp:
        _get_artifact(args.name, args).export(fp, args.path)


@catch_artifact_errors
def log(args):
    _get_artifact(args.name, args).get_log(
        sys.stdout.buffer, follow=args.follow)


@catch_artifact_errors
def input_parameters(args):
    params = _get_artifact(args.name, args).get_input_parameters()
    json.dump(params, sys.stdout, indent=True)
    print()


def setup_parser(subparsers):

    parser = subparsers.add_parser('artifact', help="Manage artifacts")

    subparser = parser.add_subparsers(
        dest='action', help="Action to be performed, no action will list")

    parser.set_defaults(func=list_all)

    delete_parser = subparser.add_parser(
        'delete', help="Delete an existing artifact")
    p = delete_parser.add_argument(
        'names', nargs='+', help="Name of the artifact to be deleted")
    p.completer = ArtifactsCompleter()
    delete_parser.set_defaults(func=delete)

    completed_parser = subparser.add_parser(
        'status', help="Return the current status an artifact")
    p = completed_parser.add_argument('name', help="Name of the artifact")
    p.completer = ArtifactsCompleter()
    completed_parser.set_defaults(func=status)

    export_parser = subparser.add_parser(
        'export', help="Download an artifact")
    p = export_parser.add_argument('name', help="Name of the artifact")
    p.completer = ArtifactsCompleter()
    export_parser.add_argument(
        '--path', help="Optional path in the artifact output")
    export_parser.add_argument(
        '--output-file', required=True, help="Path to file that will contain the artifact")
    export_parser.set_defaults(func=export)

    log_parser = subparser.add_parser(
        'log', help="Download the creation logs for an artifact")
    p = log_parser.add_argument('name', help="Name of the artifact")
    p.completer = ArtifactsCompleter()
    log_parser.add_argument('--follow', help="Follow the log until the artifact is complete",
                            action='store_true', default=False)
    log_parser.set_defaults(func=log)

    input_params_parser = subparser.add_parser(
        'input-params', help="Show the creation parameters of the artifact")
    p = input_params_parser.add_argument(
        'name', help="Name of the artifact")
    p.completer = ArtifactsCompleter()
    input_params_parser.set_defaults(func=input_parameters)
