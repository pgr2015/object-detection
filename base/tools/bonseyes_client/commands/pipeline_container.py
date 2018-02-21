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


from bonseyes.api import Pipeline, ProxiedContainerResolver
from bonseyes_client.commands.artifact_container import list_create_params, create, delete, status, log, list_all


def list_pipeline_containers(args):

    resolver = ProxiedContainerResolver(
        args.gateway_host, args.gateway_port)

    p = Pipeline(args.container, resolver)

    for c in p.containers.all():
        print(c)


def setup_parser(subparsers):

    parser = subparsers.add_parser(
        'pipeline-container', help="Manage pipeline container")
    parser.add_argument('--container', default='pipeline',
                        help="Name of the pipeline container (default: pipeline)")

    subparser = parser.add_subparsers(
        dest='action', help="Action to be performed")
    subparser.required = True

    list_parser = subparser.add_parser(
        'list-containers', help="List the containers of this pipeline")
    list_parser.set_defaults(func=list_pipeline_containers)

    list_parser = subparser.add_parser('list-runs', help="List all runs")
    list_parser.set_defaults(func=list_all)

    params_parser = subparser.add_parser('list-create-params', help="List the parameters required to start " +
                                                                    "the pipeline")

    params_parser.set_defaults(
        func=list_create_params)

    create_parser = subparser.add_parser(
        'start', help="Start a new pipeline run")
    create_parser.add_argument(
        '--parameters', help="JSON formatted map with the parameters")
    create_parser.add_argument('--input-file', nargs='*', help="Files that need to be uploaded, " +
                                                               "format is parameter_name=path/to/file")
    create_parser.add_argument('--name', required=True, help="Name of the run that will be created " +
                                                             "(must not already exist)")
    create_parser.set_defaults(func=create)

    delete_parser = subparser.add_parser(
        'delete-run', help="Delete an existing run")
    delete_parser.add_argument(
        '--name', required=True, help="Name of the runto be deleted")
    delete_parser.set_defaults(func=delete)

    completed_parser = subparser.add_parser(
        'run-status', help="Return the current status a run")
    completed_parser.add_argument(
        '--name', required=True, help="Name of the run")
    completed_parser.set_defaults(func=status)

    log_parser = subparser.add_parser(
        'run-log', help="Download the logs of a run")
    log_parser.add_argument('--name', required=True,
                            help="Name of the run")
    log_parser.set_defaults(func=log)

    return subparser
