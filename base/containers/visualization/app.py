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
import os

from io import BytesIO

from bonseyes.api import Artifact
from flask import Flask, jsonify, request
import requests


app = Flask(__name__, instance_path='/tmp')


class ScalarPluginTag:
    def __init__(self, name, view):
        self.name = name
        self.view = view

    @property
    def data(self):

        fd = BytesIO()
        self.view.export(fd)

        results = []

        for result in fd.getvalue().decode('utf-8').strip().split('\n'):
            result = result.split(' ')
            results.append([float(result[0]), int(
                float(result[1])), float(result[2])])

        return results


class ScalarPluginData:

    def __init__(self, artifact):
        self.name = 'scalars'
        self.artifact = artifact

    def tags(self):
        for metric_name in self.artifact.metric_names():

            metric = self.artifact.metric(metric_name)

            if 'scalar' not in metric.view_names():
                continue

            yield ScalarPluginTag(metric_name, metric.view('scalar'))

    def tag(self, tag):
        return ScalarPluginTag(tag, self.artifact.metric(tag).view('scalar'))


class Run:

    def __init__(self, name, url):
        self.name = name
        self.artifact = Artifact(url)
        self.plugins_data = {'scalars': ScalarPluginData(self.artifact)}

    def plugins(self):
        return self.plugins_data.values()

    def plugin(self, plugin):
        return self.plugins_data[plugin]


class Runs:

    def __init__(self):
        self.runs_data = {}

    def runs(self):
        req = requests.get('http://' + os.environ['PIPELINE'] + '/artifacts')

        if req.status_code != 200:
            raise Exception("Error while getting artifact list")

        for artifact_data in req.json():
            yield Run(artifact_data['container'] + "/" + artifact_data['name'],
                      'http://' + artifact_data['container'] + artifact_data['href'])

    def run(self, run_name):
        container, name = run_name.split("/")

        req = requests.get('http://' + container + '/')

        if req.status_code != 200:
            raise Exception("Error while getting artifact list")

        return Run(run_name, 'http://' + container + req.json()['artifacts'][0] + '/' + name)


runs = Runs()


@app.route('/tensorboard/data/logdir')
def logdir_route():
    return jsonify({'logdir': '/data/logs'})


@app.route('/tensorboard/data/runs')
def runs_route():

    ret = {}

    for run in runs.runs():
        ret[run.name] = {'firstEventTimestamp': 0}

        for plugin in run.plugins():
            ret[run.name][plugin.name] = [x.name for x in plugin.tags()]

    return jsonify(ret)


@app.route('/tensorboard/data/scalars')
def scalars_route():
    run = request.args.get('run')
    tag = request.args.get('tag')

    return jsonify(runs.run(run).plugin('scalars').tag(tag).data)


@app.route('/tensorboard/data/plugin/text/runs')
def plugin_text_runs_route():
    return jsonify([])
