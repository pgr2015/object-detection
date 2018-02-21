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

import subprocess
from tempfile import TemporaryDirectory

import sys
import json

from bonseyes.api import ArtifactFailedException
from bonseyes_client.utils import get_artifact_list, open_input_files

CONTAINER_CID = 'container.cid'
IMAGE_ID = 'image.id'

START_BOLD = '\033[1m'
END_BOLD = '\033[0m'

def run(args):

    with TemporaryDirectory() as tmp_dir:

        if args.f is not None:

            print(START_BOLD + 'Building image...' + END_BOLD)
            print(START_BOLD + '-----------------------' + END_BOLD)

            iid_file = os.path.join(tmp_dir, IMAGE_ID)

            subprocess.check_call(['docker', 'build', '--iidfile', iid_file, '-f', args.f, '.'])
            with open(iid_file) as fp:
                args.image = fp.read()

            print(START_BOLD + 'Build image complete' + END_BOLD)
            print()

        if args.gpu:
            command = ['docker']
        else:
            command = ['nvidia-docker']

        cid_file = os.path.join(tmp_dir, CONTAINER_CID)

        command += ['run', '-p', '80', '-d', '--cidfile', cid_file]

        if not args.no_rm:
            command += ['--rm']

        command += [args.image]

        # start the container
        print(START_BOLD + 'Starting container...' + END_BOLD)
        print(START_BOLD + '-----------------------' + END_BOLD)
        subprocess.check_call(command)
        print(START_BOLD + 'Container started' + END_BOLD)
        print()

        # read back the container id
        with open(cid_file) as fp:
            cid = fp.read()

        try:

            # find the host and port where the container is listening
            print(START_BOLD + 'Mapping port...' + END_BOLD)
            print(START_BOLD + '-----------------------' + END_BOLD)
            host, port = subprocess.check_output(['docker', 'port', cid, '80']).decode("utf-8").split(':')
            print(START_BOLD + 'Port mapped' + END_BOLD)
            print()

            # open all input files to prepare to send them
            input_files = open_input_files(args.input_file)

            # parse all input parameters
            json_data = {}

            if args.parameters:
                json_data = json.loads(args.parameters)

            # get the artifact list of the container
            full_args = argparse.Namespace(container=port, **args.__dict__)
            artifact_list = get_artifact_list(full_args)

            # create the artifact
            artifact = artifact_list.create("default", json_data, input_files)

            # wait until complete or failed
            failed = False

            try:
                artifact.wait_for_completed()
            except ArtifactFailedException:
                failed = True

            # print out the logs
            print()
            print(START_BOLD + '--- Start log ---' + END_BOLD)
            artifact.get_log(sys.stdout.buffer)
            print(START_BOLD + '--- End log ---' + END_BOLD)
            print()

            # exit according to the status of the artifact
            if failed:
                raise Exception('Failed to build artifact')
            else:
                # write out the results
                if args.output_file is not None:
                    print(START_BOLD + 'Downloading output...' + END_BOLD)
                    print(START_BOLD + '-----------------------' + END_BOLD)
                    with open(args.output_file, 'wb') as fp:
                        artifact.export(fp)
                    print(START_BOLD + 'Output downloaded' + END_BOLD)
                    print()

        finally:

            if args.container_logs:
                print()
                print(START_BOLD + '--- Start container log ---' + END_BOLD)
                subprocess.check_call(['docker', 'logs', cid])
                print(START_BOLD + '--- End container log ---' + END_BOLD)
                print()

            if not args.no_stop:
                print(START_BOLD + 'Stopping container...' + END_BOLD)
                print(START_BOLD + '-----------------------' + END_BOLD)
                subprocess.check_call(['docker', 'stop', cid])
                print(START_BOLD + 'Container stopped' + END_BOLD)


def setup_parser(subparsers):
    parser = subparsers.add_parser('run', help="Run an image and create an artifact with it")
    parser.add_argument('--gpu', action="store_true",
                        help="Give gpu access to container")
    parser.add_argument('-f', help="Docker file used to build the container")
    parser.add_argument('--no-stop', help="Delete container when done", action="store_true")
    parser.add_argument('--no-rm', help="Do not delete container when done", action="store_true")
    parser.add_argument('--container-logs', help="Show all container logs", action="store_true")
    parser.add_argument(
        '--output-file', help="Exports the completed artifact to the specified file")
    parser.add_argument(
        '--parameters', help="JSON formatted map with the parameters")

    parser.add_argument('--input-file', nargs='*', help="Files that need to be uploaded, " +
                                                               "format is parameter_name=path/to/file")

    parser.add_argument('--image', help="Name of the container image to start")

    parser.set_defaults(func=run)
