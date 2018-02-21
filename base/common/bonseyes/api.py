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
from urllib.parse import urljoin

import requests
import json

import time


class ArtifactException(Exception):
    def __init__(self, *args, **kwargs):
        super(ArtifactException, self).__init__(*args, **kwargs)


class ArtifactNotFoundException(ArtifactException):
    def __init__(self, *args, **kwargs):
        super(ArtifactNotFoundException, self).__init__(*args, **kwargs)


class ArtifactFailedException(ArtifactException):
    def __init__(self, *args, **kwargs):
        super(ArtifactFailedException, self).__init__(*args, **kwargs)


class MetricView:

    def __init__(self, url):
        self.url = url

    def export(self, fp):

        ret = requests.get(self.url, stream=True)

        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException('Unable to export (error code %d)' %
                                    ret.status_code)

        for chunk in ret.iter_content(chunk_size=1024):
            if chunk:
                fp.write(chunk)


class Metric:
    def __init__(self, url):
        self.url = url

        if self.url[-1] != '/':
            self.url = self.url + '/'

    def view_names(self):
        ret = requests.get(self.url)

        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException(
                'Cannot retrieve status (error code %d)' % ret.status_code)

        return ret.json()

    def views(self):
        return [MetricView(self.url + view) for view in self.view()]

    def view(self, name):
        return MetricView(self.url + name)


class SimpleContainerResolver:

    def __init__(self):
        pass

    def container_url(self, name):
        return 'http://%s' % name


class CustomContainerResolver:

    def __init__(self, urls):
        self.urls = urls

    def container_url(self, name):
        return self.urls[name]


class ProxiedContainerResolver:

    def __init__(self, gateway_host, gateway_port):
        self.gateway_host = gateway_host
        self.gateway_port = gateway_port

    def container_url(self, name):
        return 'http://%s:%s/containers/%s' % (self.gateway_host, str(self.gateway_port), name)


class Artifact:

    STATUS_COMPLETED = 'completed'
    STATUS_IN_PROGRESS = 'in-progress'
    STATUS_FAILED = 'failed'

    def __init__(self, url):
        self.url = url.rstrip('/')

    def wait_for_completed(self):

        while True:

            status = self.get_status()

            time.sleep(1)

            if status == 'completed':
                return
            elif status == 'failed':
                raise ArtifactFailedException(
                    'Artifact failed while waiting for completion')

    def delete(self):
        ret = requests.delete(self.url + '/')
        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException(
                'Cannot retrieve status (error code %d)' % ret.status_code)

    def get_status(self):
        ret = requests.get(self.url + '/status')

        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException(
                'Cannot retrieve status (error code %d)' % ret.status_code)

        return ret.json()['result']

    def export(self, fp, path=None):

        url = self.url + '/data'

        if path is not None:
            url = url + '/' + path

        ret = requests.get(url, stream=True)

        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException('Unable to export (error code %d)' %
                                    ret.status_code)

        for chunk in ret.iter_content(chunk_size=1024):
            if chunk:
                fp.write(chunk)

    def get_log(self, fp, follow=False):

        if follow:
            ret = requests.get(self.url + '/log?follow', stream=True)
        else:
            ret = requests.get(self.url + '/log', stream=True)

        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to download log (error code %d)' % ret.status_code)

        for chunk in ret.iter_content():
            if chunk:
                fp.write(chunk)

    def get_input_parameters(self):
        ret = requests.get(self.url + '/input_parameters')

        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to download log (error code %d)' % ret.status_code)

        return ret.json()

    def metric_names(self):
        ret = requests.get(self.url + '/metrics/')

        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to download log (error code %d)' % ret.status_code)

        return ret.json()

    def metrics(self):
        metrics = []

        for metric in self.metric_names():
            m = Metric(self.url + '/metrics/' + metric + '/')
            metrics.append(m)

        return metrics

    def metric(self, name):
        return Metric(self.url + '/metrics/' + name + '/')


class DataSet(Artifact):

    def __init__(self, url):
        Artifact.__init__(self, url)

    @property
    def samples(self):
        ret = requests.get(self.url + '/data/dataset.json')

        if ret.status_code == 404:
            raise ArtifactNotFoundException()

        if ret.status_code != 200:
            raise ArtifactException(
                'Cannot retrieve status (error code %d)' % ret.status_code)

        samples_data = ret.json()

        # resolve all relative urls in the data and views
        for sample_name, sample in samples_data.items():

            if 'data' in sample:
                for data_name, data_value in sample['data'].items():
                    sample['data'][data_name] = urljoin(
                        self.url + '/data/', data_value)

            if 'views' in sample:
                for data_name, data_value in sample['views'].items():
                    sample['views'][data_name] = urljoin(
                        self.url + '/data/', data_value)

        return samples_data


class ArtifactList:
    def __init__(self, url):
        self.url = url

    def create(self, name, parameters, files={}):

        files = dict(files)

        files['name'] = (None, name, None)
        files['data'] = (None, json.dumps(parameters), 'application/json')

        ret = requests.post(self.url, files=files)

        if ret.status_code != 200:
            raise ArtifactException('Unable to create (error code %d)' %
                                    ret.status_code)

        return self.get(name)

    def list_all(self):
        ret = requests.get(self.url)

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to list (error code %d)' % ret.status_code)

        return ret.json()

    def all(self):
        return [self.get(name) for name in self.list_all()]

    def get(self, name):
        return Artifact(self.url + name)


class Container:
    def __init__(self, url):
        if url.startswith('http://'):
            self.url = url
        else:
            self.url = SimpleContainerResolver().container_url(url)

    @property
    def artifact_path(self):
        ret = requests.get(self.url + '/')

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to list (error code %d)' % ret.status_code)

        return ret.json()['artifacts'][0].rstrip('/') + '/'

    @property
    def artifacts(self):

        ret = requests.get(self.url + '/')

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to list (error code %d)' % ret.status_code)

        return ArtifactList(self.url + self.artifact_path)

    @property
    def create_params(self):

        ret = requests.get(self.url + '/')

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to list (error code %d)' % ret.status_code)

        print(json.dumps(ret.json()['parameters'], indent=4))


class ContainerList:
    def __init__(self, url, resolver):
        self.url = url
        self.resolver = resolver

    def all(self):
        ret = requests.get(self.url)

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to list (error code %d)' % ret.status_code)

        return [x['name'] for x in ret.json()]

    def get(self, name):
        return Container(self.resolver.container_url(name))


class Pipeline:
    def __init__(self, name, resolver):
        self.resolver = resolver
        self.name = name

    @property
    def containers(self):
        return ContainerList(self.resolver.container_url(self.name) + '/containers', self.resolver)

    @property
    def runs(self):
        return ArtifactList(self.resolver.container_url(self.name) + '/runs')


class Dashboard:
    def __init__(self, resolver=SimpleContainerResolver()):
        self.resolver = resolver

    @property
    def containers(self):
        ret = requests.get(self.resolver.container_url(
            'dashboard').rstrip('/') + "/containers")

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to list containers (error code %d)' % ret.status_code)

        return ret.json()

    @property
    def pipeline_names(self):
        ret = requests.get(self.resolver.container_url(
            'dashboard').rstrip('/') + "/pipelines/")

        if ret.status_code != 200:
            raise ArtifactException(
                'Unable to list (error code %d)' % ret.status_code)

        return [x['container'] for x in ret.json()]
