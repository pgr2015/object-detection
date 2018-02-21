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
import glob
import os

import sys

import subprocess

MAIN_BUILD_FILE = "docker-compose-build.yml"
BASE_BUILD_FILE = os.path.join("base", "docker-compose-build.yml")
COMPONENTS_DIR = "components"
BUILD_FILE = "docker-compose-build.yml"


def build(args):

    if not os.path.exists(MAIN_BUILD_FILE):
        sys.stderr.write(
            'Error: The main build file %s is missing.\n' % MAIN_BUILD_FILE)
        sys.exit(1)

    if not os.path.exists(BASE_BUILD_FILE):
        sys.stderr.write(
            'Error: The base build file %s is missing\n' % BASE_BUILD_FILE)
        sys.exit(1)

    command = ["docker-compose", "-f",
               MAIN_BUILD_FILE, "-f", BASE_BUILD_FILE]

    for plugin in glob.glob(os.path.join(COMPONENTS_DIR, '*', BUILD_FILE)):
        command.extend(['-f', plugin])

    command += ['build']

    if args.containers is not None:
        for container in args.containers:
            command.append(container)

    environ = dict(os.environ)
    environ['IMAGE_TAG'] = args.tag

    subprocess.check_call(command, env=environ)


def setup_parser(subparsers):
    parser = subparsers.add_parser('build', help="Build containers")
    parser.add_argument('--tag', '-t', required=True,
                        help="Tag used to mark all images", default="latest")
    parser.add_argument('containers', nargs=argparse.REMAINDER,
                        help="Name of the containers to build")
    parser.set_defaults(func=build)
