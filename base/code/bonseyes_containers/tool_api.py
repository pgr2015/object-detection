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
import logging
import socket
import zipfile
import time
from io import BytesIO

import requests
import uwsgidecorators
from flask import request, jsonify
from flask.app import Flask
from flask.views import MethodView
from flask.helpers import send_file
import tempfile
import os
import json

from flask.wrappers import Response

from bonseyes_containers.local_artifacts import LocalArtifact, LocalArtifactList
from bonseyes_containers.utils import no_cache

import uwsgi


@uwsgidecorators.postfork
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    if uwsgi.worker_id() != 0:
        format_prefix = "[pid: %d|worker: %d]" % (
            os.getpid(), uwsgi.worker_id())
    elif uwsgi.mule_id() != 0:
        format_prefix = "[pid: %d|mule: %d]" % (os.getpid(), uwsgi.mule_id())
    else:
        format_prefix = "[pid: %d|other]" % os.getpid()

    formatter = logging.Formatter(
        format_prefix + ' %(asctime)s %(name)s:%(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class Data(MethodView):

    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, name, path=None):
        artifact = self.artifact_list.get(name)

        if not artifact.exists():
            return "Not found", 404

        if artifact.status != LocalArtifact.STATUS_COMPLETED:
            return "Not found", 404

        if os.path.isdir(artifact.get_data(path)):

            def generate_zip():
                class OutputStream:
                    def __init__(self):
                        self.pos = 0
                        self.buffer = BytesIO()

                    def tell(self):
                        return self.pos

                    def write(self, data):
                        self.pos += len(data)
                        self.buffer.write(data)

                    def get_data(self):
                        data = self.buffer.getvalue()
                        self.buffer.truncate()
                        return data

                    def flush(self):
                        pass

                out = OutputStream()

                with zipfile.ZipFile(out, 'w') as z:
                    for root, dirs, files in os.walk(artifact.get_data(path)):
                        for f in files:
                            filename = os.path.join(root, f)
                            z.write(filename, arcname=os.path.relpath(
                                filename, artifact.get_data(path)))
                            logging.info("Returning %d bytes for file %s" % (out.pos, filename))
                            yield out.get_data()

                logging.info("Returning last %d bytes" % out.pos)
                yield out.get_data()

            return Response(generate_zip(), mimetype='application/zip')

        else:
            return send_file(artifact.get_data(path))


class MetricView(MethodView):
    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, name, metric_name, view_name):

        artifact = self.artifact_list.get(name)

        if not artifact.exists():
            return "Not found", 404

        metric = artifact.metric(metric_name)

        if metric is None:
            return "Not found", 404

        metric_view = metric.view(view_name)

        if metric_view is None:
            return "Not found", 404

        return send_file(metric_view.view_file)


class Metric(MethodView):
    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, name, metric_name):

        artifact = self.artifact_list.get(name)

        if not artifact.exists():
            return "Not found", 404

        metric = artifact.metric(metric_name)

        if metric is None:
            return "Not found", 404

        return jsonify(metric.view_names)


class MetricList(MethodView):
    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, name):

        artifact = self.artifact_list.get(name)

        if not artifact.exists():
            return "Not found", 404

        return jsonify(artifact.metric_names)


class Status(MethodView):

    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, name):
        artifact = self.artifact_list.get(name)

        if not artifact.exists():
            return "Not found", 404

        return jsonify({'result': artifact.status})


class Log(MethodView):

    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, name):
        artifact = self.artifact_list.get(name)

        if not artifact.exists():
            return "Not found", 404

        if 'follow' in request.args and artifact.status == LocalArtifact.STATUS_IN_PROGRESS:

            def follow_file():
                with open(artifact.log_file, 'r') as log:
                    while artifact.status == LocalArtifact.STATUS_IN_PROGRESS:
                        where = log.tell()
                        line = log.readline()
                        if not line:
                            time.sleep(1)
                            log.seek(where)
                        else:
                            yield line

                    yield log.read()

            return Response(follow_file(), mimetype='text/plain')

        else:
            return send_file(artifact.log_file,  mimetype='text/plain')


class InputParameters(MethodView):

    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, name):
        artifact = self.artifact_list.get(name)

        if not artifact.exists():
            return "Not found", 404

        return send_file(artifact.input_parameters, mimetype='application/json')


class InputFileList(MethodView):

    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, name):
        artifact = self.artifact_list.get(name)
        return jsonify(artifact.input_files_list)


class InputFile(MethodView):

    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self, artifact_name, input_file_name):
        artifact = self.artifact_list.get(artifact_name)

        if not artifact.exists():
            return "Artifact not found", 404

        if input_file_name not in artifact.input_files_list:
            return "Input file not found", 404

        return send_file(artifact.get_input_file(input_file_name))


class Artifact(MethodView):

    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    def delete(self, name):
        artifact = self.artifact_list.get(name)

        if not artifact.exists():
            return "Not found", 404

        artifact.delete()

        return jsonify({'result': 'success'})


class List(MethodView):

    def __init__(self, artifact_list):
        MethodView.__init__(self)
        self.artifact_list = artifact_list

    @no_cache()
    def get(self):
        return jsonify(self.artifact_list.list_all())

    def post(self):
        if 'name' not in request.form:
            raise Exception('Invalid request')

        input_files = {}

        # save the input files to temporary files
        for f in request.files:
            fd, file_name = tempfile.mkstemp()
            with os.fdopen(fd, 'wb') as fd:
                request.files[f].save(fd)

            input_files[f] = file_name

        # load the additional arguments
        if 'data' in request.form:
            input_params = json.loads(request.form['data'])
        else:
            input_params = {}

        self.artifact_list.create(
            request.form['name'], input_params, input_files)

        return jsonify({'result': 'success'})


class ContainerDescription(MethodView):
    def __init__(self, data):
        self.data = data

    @no_cache()
    def get(self):
        return jsonify(self.data)


def register_api(app, endpoint, name, create_function, extra_args=None):

    artifact_list = LocalArtifactList('/data', create_function, extra_args)

    # mark all artifacts that are still marked in progress to be failed
    for artifact in artifact_list.artifacts():
        if artifact.status == LocalArtifact.STATUS_IN_PROGRESS:
            artifact.set_status(LocalArtifact.STATUS_FAILED)

    app.add_url_rule(endpoint + '/',
                     view_func=List.as_view(name + '_list', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/',
                     view_func=Artifact.as_view(name, artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/log',
                     view_func=Log.as_view(name + '_log', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/data',
                     view_func=Data.as_view(name + '_data', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/metrics/',
                     view_func=MetricList.as_view(name + '_metric_list', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/metrics/<string:metric_name>/',
                     view_func=Metric.as_view(name + '_metric', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/metrics/<string:metric_name>/<string:view_name>',
                     view_func=MetricView.as_view(name + '_metric_view', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/data/<path:path>',
                     view_func=Data.as_view(name + '_data_item', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/input_parameters',
                     view_func=InputParameters.as_view(name + '_input_parameters', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/input_files/',
                     view_func=InputFileList.as_view(name + '_input_file_list', artifact_list))

    app.add_url_rule(endpoint + '/<string:artifact_name>/input_files/<string:input_file_name>',
                     view_func=InputFile.as_view(name + '_input_file', artifact_list))

    app.add_url_rule(endpoint + '/<string:name>/status',
                     view_func=Status.as_view(name + '_status', artifact_list))


def create_app(create_function, description, parameters, output_type, extra_args=None):
    app = Flask(__name__, instance_path='/tmp')

    register_api(app, '/artifacts', 'artifacts', create_function, extra_args)

    container_desc = {'description': description,
                      'artifacts': ['/artifacts'],
                      'parameters': parameters,
                      'output_type': output_type}

    desc_view = ContainerDescription.as_view('description', container_desc)
    app.add_url_rule('/', view_func=desc_view)

    # register the container with the dashboard
    try:
        requests.post('http://dashboard/containers/',
                      json={'name': socket.gethostname()})
    except requests.exceptions.ConnectionError:
        logging.error('Unable to register container in dashboard')

    return app
