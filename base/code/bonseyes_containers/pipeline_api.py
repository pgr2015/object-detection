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

import requests
from flask import Flask, jsonify, request
from flask.views import MethodView

import bonseyes
import bonseyes.api
import bonseyes_containers
from bonseyes_containers.tool_api import ContainerDescription
from bonseyes_containers.utils import no_cache

CONTAINER_CATEGORY_DATA = 'data'
CONTAINER_CATEGORY_MODEL = 'model'
CONTAINER_CATEGORY_PIPELINE = 'pipeline'
CONTAINER_CATEGORY_OTHER = 'other'

CONTAINER_STATUS_MISSING = 'missing'
CONTAINER_STATUS_STARTED = 'started'
CONTAINER_STATUS_STOPPED = 'stopped'


class ArtifactList(MethodView):

    def __init__(self, containers):
        self.containers = containers

    @no_cache()
    def get(self):

        results = []

        for name, value in self.containers.items():

            if request.args.get('type') is not None:
                if value['type'] != request.args.get('type'):
                    continue

            try:
                ret = requests.get('http://' + name)
            except requests.exceptions.ConnectionError:
                logging.error("Unable to contact " + name)
                continue

            if ret.status_code != 200:
                continue

            container = ret.json()

            if request.args.get('output_type') is not None:
                if container['output_type'] != request.args.get('output_type'):
                    continue

            for endpoint in container['artifacts']:

                ret = requests.get('http://' + name + endpoint)

                if ret.status_code != 200:
                    continue

                for artifact in ret.json():

                    href = endpoint + '/' + artifact

                    ret = requests.get('http://' + name + href + '/status')

                    if ret.status_code != 200:
                        continue

                    status = ret.json()['result']

                    if request.args.get('status') is not None:
                        if status != request.args.get('status'):
                            continue

                    results.append({'name': artifact,
                                    'container': name,
                                    'href': href,
                                    'status': status,
                                    'output_type': container['output_type'],
                                    'type': value['type']})

        return jsonify(results)


class ContainerList(MethodView):

    def __init__(self, containers):
        self.containers = containers

    @no_cache()
    def get(self):

        results = []

        for name, value in self.containers.items():

            if request.args.get('type') is not None:
                if value['type'] != request.args.get('type'):
                    continue

            container = dict(value)
            container['name'] = name

            ret = requests.get('http://' + name)

            if ret.status_code != 200:
                continue

            container['info'] = ret.json()

            results.append(container)

        return jsonify(results)

    def post(self):
        content = request.get_json()

        if content['action'] == 'start_all':
            for container in self.containers.values():
                container['status'] = CONTAINER_STATUS_STARTED
        elif content['action'] == 'stop_all':
            for container in self.containers.values():
                container['status'] = CONTAINER_STATUS_STOPPED
        elif content['action'] == 'remove_all':
            for container in self.containers.values():
                container['status'] = CONTAINER_STATUS_MISSING
        elif content['action'] == 'restart_all':
            for container in self.containers.values():
                container['status'] = CONTAINER_STATUS_STARTED

        return jsonify({'result': 'success'})


class Container(MethodView):

    def __init__(self, containers):
        self.containers = containers

    @no_cache()
    def get(self, container_name):
        return jsonify(self.containers[container_name])

    def post(self, container_name):
        content = request.get_json()

        if content['action'] == 'start':
            self.containers[container_name]['status'] = CONTAINER_STATUS_STARTED
        elif content['action'] == 'restart':
            self.containers[container_name]['status'] = CONTAINER_STATUS_STARTED
        elif content['action'] == 'stop':
            self.containers[container_name]['status'] = CONTAINER_STATUS_STOPPED
        elif content['action'] == 'remove':
            self.containers[container_name]['status'] = CONTAINER_STATUS_MISSING

        return jsonify({'result': 'success'})


class Task(MethodView):

    def __init__(self, task):
        self.task = task

    @no_cache()
    def get(self):
        return jsonify(self.task)


def create_artifact_if_not_complete(container_name, name, params, files={}):

    container = bonseyes.api.Container(container_name)

    if name in container.artifacts.list_all():

        artifact = container.artifacts.get(name)

        if artifact.get_status() != bonseyes.api.Artifact.STATUS_FAILED:
            return artifact

        artifact.delete()

    return container.artifacts.create(name, parameters=params, files=files)


def create_pipeline_app(task, containers, run_function, description, parameters, output_type):

    app = Flask(__name__, instance_path='/tmp')

    containers_state = {}

    for container, value in containers.items():
        containers_state[container] = dict(value)
        containers_state[container]['status'] = CONTAINER_STATUS_MISSING

    app.add_url_rule('/task', view_func=Task.as_view('task', task))
    app.add_url_rule(
        '/artifacts', view_func=ArtifactList.as_view('artifact_list', containers_state))
    app.add_url_rule(
        '/containers', view_func=ContainerList.as_view('containers', containers_state))
    app.add_url_rule('/containers/<string:container_name>',
                     view_func=Container.as_view('container', containers_state))

    container_desc = {'description': description,
                      'artifacts': ['/runs'],
                      'parameters': parameters,
                      'output_type': output_type}

    desc_view = ContainerDescription.as_view('description', container_desc)
    app.add_url_rule('/', view_func=desc_view)

    bonseyes_containers.tool_api.register_api(
        app, '/runs', 'runs', run_function)

    # register the container with the dashboard
    try:
        requests.post('http://dashboard/containers/',
                      json={'name': socket.gethostname()})
    except requests.exceptions.ConnectionError:
        logging.error('Unable to register container in dashboard')

    return app
