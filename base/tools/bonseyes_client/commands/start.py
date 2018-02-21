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
import argparse
import os

import sys

import subprocess

COMPOSE_FILE = "docker-compose.yml"
COMPOSE_TEMPLATE = "docker-compose.yml.jinja"


def start(args):

    if args.gpu or os.path.exists(COMPOSE_TEMPLATE):
        command = ['nvidia-docker-compose']
    else:
        command = ['docker-compose']

    if os.path.exists(COMPOSE_TEMPLATE):
        command = command + ['-t', COMPOSE_TEMPLATE]
    elif os.path.exists(COMPOSE_FILE):
        command = command + ['-f', COMPOSE_FILE]
    else:
        sys.stderr.write('Error: Cannot find %s nor %s\n' %
                         (COMPOSE_TEMPLATE, COMPOSE_FILE))
        sys.exit(1)

    command += ['-p', args.project, 'up', '-d']

    if args.containers is not None:
        for container in args.containers:
            command.append(container)

    environ = dict(os.environ)

    if args.tag is not None:
        environ['IMAGE_TAG'] = args.tag
    else:
        environ['IMAGE_TAG'] = 'latest'

    subprocess.check_call(command, env=environ)


def setup_parser(subparsers):
    parser = subparsers.add_parser('start', help="Start containers")
    parser.add_argument('--gpu', action="store_true",
                        help="Give gpu access to containers")
    parser.add_argument('--project', '-p', required=True,
                        help="Name of the project")
    parser.add_argument('--tag', '-t', help="Tag of images to use")
    parser.add_argument('containers', nargs=argparse.REMAINDER,
                        help="Name of the containers to start")
    parser.set_defaults(func=start)
