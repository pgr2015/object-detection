import logging
import os
import tempfile

import subprocess

from bonseyes.api import Artifact
from bonseyes_containers.tool_api import create_app


def download_artifact(url, local_path):

    logging.info("Downloading %s to %s" % (url, local_path))

    with open(local_path, 'wb') as fp:
        Artifact(url).export(fp)

    logging.info("Downloaded %d bytes", os.path.getsize(local_path))


def start_external_program(artifact, input_data, input_files, command, parameters):

    with tempfile.TemporaryDirectory() as tmp_dir:

        full_command = [command]

        for parameter, config in parameters.items():
            if config['type'] == 'string':
                if parameter not in input_data:
                    raise Exception('Missing parameter ' + parameter)
                full_command += ['--' + parameter, input_data[parameter]]

            elif config['type'] == 'file':
                if parameter not in input_files:
                    raise Exception('Missing parameter ' + parameter)
                full_command += ['--' + parameter, input_files[parameter]]

            elif config['type'] == 'artifact':

                if parameter not in input_data:
                    raise Exception('Missing parameter ' + parameter)

                tmp_file = os.path.join(tmp_dir, parameter)
                download_artifact(input_data[parameter], tmp_file)
                full_command += ['--' + parameter, tmp_file]

        full_command += [artifact.data_file]

        process = subprocess.Popen(full_command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        for line in process.stdout:
            logging.info("command: " + line.decode('utf-8', 'ignore').strip())

        process.wait()

        if process.returncode != 0:
            raise Exception("Error while executing program (exit code %d)", process.returncode)


def create_external_executable_tool(command, parameters, description, output_type):

    extra_args = {'parameters': parameters, 'command': command}

    return create_app(start_external_program, description, parameters, output_type, extra_args=extra_args)

