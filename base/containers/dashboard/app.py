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
import re

import requests
from flask import Flask, redirect, url_for, jsonify
import os

from flask.globals import request
from flask.wrappers import Response

from bonseyes_containers.utils import no_cache

app = Flask(__name__, instance_path='/tmp')


@app.route('/containers/<string:container>/<string:artifact_list>/<string:artifact>/log')
def proxy_logs(container, artifact_list, artifact):

    base_url = 'http://%s/%s/%s/log' % (container, artifact_list, artifact)

    if request.query_string != b'':
        base_url += '?' + request.query_string.decode('utf-8')

    req = requests.get(base_url, stream=True)

    return Response(req.iter_content(), content_type=req.headers['content-type'])


@app.route('/pipelines/')
@no_cache()
def pipelines():

    results = []

    for container in os.environ['PIPELINES'].split(':'):
        ret = requests.get('http://' + container)
        results.append(
            {'name': ret.json()['description'], 'container': container})

    return jsonify(results)


CONTAINERS_DIR = '/containers'


@app.route('/containers/', methods=['GET', 'POST'])
def containers():
    if request.method == 'POST':
        data = request.json

        if not re.match('^[a-zA-Z0-9_-]+$', data['name']):
            return 'Invalid hostname', 500

        with open(os.path.join(CONTAINERS_DIR, data['name']), 'w') as _:
            pass

        return jsonify({'result': 'success'})

    else:

        results = {}

        for container in os.listdir(CONTAINERS_DIR):

            req = requests.get("http://" + container)

            if req.status_code != 200:
                logging.error('Container ' + container +
                              ' cannot be contacted, removing')
                os.unlink(os.path.join(CONTAINERS_DIR, container))

            results[container] = req.json()

        return jsonify(results)


@app.route('/')
def index():
    return redirect(url_for('static', filename='index.html'), code=302)
