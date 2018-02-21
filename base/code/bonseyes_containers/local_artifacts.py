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

import json
import logging

import os
import re

import shutil
import time

import sys

from uwsgidecorators import mulefunc

from bonseyes_containers.utils import load_callable, get_full_name


@mulefunc
def create_artifact(create_func, artifact_list_path, artifact_name, **kwargs):

    artifact = LocalArtifactList(artifact_list_path).get(artifact_name)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.FileHandler(artifact.log_file, mode='w')
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    try:

        logger.info("Starting...")

        kwargs['artifact'] = artifact

        create_func_callable = load_callable(create_func)

        create_func_callable(**kwargs)

        logger.info("Finished.")

        artifact.set_status(LocalArtifact.STATUS_COMPLETED)

    except Exception as e:
        logger.exception('Error while processing')

        artifact.set_status(LocalArtifact.STATUS_FAILED)

        raise

    finally:
        ch.close()
        logger.removeHandler(ch)

    # exit the mule process to make sure we clean up any allocated resource
    sys.exit(0)


class LocalArtifactList:

    def __init__(self, storage_path, create_function=None, extra_args=None):
        self.storage_path = storage_path
        self.create_function = create_function
        self.extra_args = extra_args

    def list_all(self):
        return os.listdir(self.storage_path)

    def artifacts(self):
        return [self.get(name) for name in self.list_all()]

    def get(self, name):
        if re.match(r'^[a-zA-Z0-9_-]+$', name) is None:
            raise Exception('Invalid name')

        return LocalArtifact(os.path.join(self.storage_path, name))

    def create(self, name, input_data, input_files):

        if self.create_function is None:
            raise Exception("Artifact creation not available")

        artifact = self.get(name)

        if artifact.exists():
            raise Exception('Artifact already exists')

        os.makedirs(artifact.storage_path)

        input_data['name'] = name

        # save the input parameters
        with open(artifact.input_parameters, 'w') as fp:
            json.dump(input_data, fp)

        # save all the input files
        os.makedirs(artifact.input_files)
        real_input_files = {}
        for key, value in input_files.items():
            new_value = os.path.join(artifact.input_files, key)
            # FIXME: security problem here
            shutil.move(value, new_value)
            real_input_files[key] = new_value

        # create an empty log file
        with open(artifact.log_file, 'w'):
            pass

        artifact.set_status(LocalArtifact.STATUS_IN_PROGRESS)

        def fqn(obj):
            if isinstance(obj, str):
                return obj
            elif isinstance(obj, int):
                return obj
            elif isinstance(obj, float):
                return obj
            elif isinstance(obj, tuple):
                return obj
            elif isinstance(obj, list):
                return obj
            elif isinstance(obj, dict):
                return obj
            elif obj is None:
                return obj
            else:
                return get_full_name(obj)

        kwargs = {}

        # add all extra params needed (converting them to strings if necessary)
        if self.extra_args is not None:
            kwargs = {key: fqn(value)
                      for (key, value) in self.extra_args.items()}

        kwargs['input_data'] = input_data
        kwargs['input_files'] = real_input_files

        # finally call the task
        create_artifact(fqn(self.create_function),
                        self.storage_path, name, **kwargs)


class MetricView:

    SCALAR_VIEW = 'scalar'

    def __init__(self, name, storage_path):
        self.storage_path = storage_path
        self.name = name

    @property
    def view_file(self):
        return self.storage_path


class Metric:

    def __init__(self, name, storage_path):
        self.storage_path = storage_path
        self.name = name

    @property
    def view_names(self):
        metrics_dir = os.path.join(self.storage_path)
        return os.listdir(metrics_dir)

    @property
    def views(self):
        metrics_dir = os.path.join(self.storage_path)
        return [MetricView(x, os.path.join(metrics_dir, x)) for x in self.view_names]

    def view(self, view_name):
        metric_view_path = os.path.join(self.storage_path, view_name)
        if os.path.exists(metric_view_path):
            return MetricView(view_name, metric_view_path)
        else:
            return None

    def create_view(self, view_name):
        metric_view_path = os.path.join(self.storage_path, view_name)
        return MetricView(view_name, metric_view_path)


class LocalArtifact:

    STATUS_COMPLETED = 'completed'
    STATUS_IN_PROGRESS = 'in-progress'
    STATUS_FAILED = 'failed'

    STATUS_FILE = 'status'
    LOG_FILE = 'log'
    DATA_FILE = 'data'
    INPUT_FILES = 'input_files'
    INPUT_PARAMETERS = 'input_parameters.json'

    METRICS_DIR = 'metrics'

    def __init__(self, storage_path):
        self.storage_path = storage_path

    def delete(self):
        if self.status == self.STATUS_IN_PROGRESS:
            raise Exception('Cannot delete artifact in progress')

        shutil.rmtree(self.storage_path)

    def exists(self):
        return os.path.exists(self.storage_path)

    @property
    def log_file(self):
        return os.path.join(self.storage_path, LocalArtifact.LOG_FILE)

    def get_data(self, path=None):
        if path is None:
            return os.path.join(self.storage_path, LocalArtifact.DATA_FILE)
        else:
            # FIXME: security problem here
            return os.path.join(self.storage_path, LocalArtifact.DATA_FILE, path)

    @property
    def input_files(self):
        return os.path.join(self.storage_path, LocalArtifact.INPUT_FILES)

    @property
    def input_files_list(self):
        return os.listdir(self.input_files)

    def get_input_file(self, name):
        return os.path.join(self.storage_path, LocalArtifact.INPUT_FILES, name)

    @property
    def input_parameters(self):
        return os.path.join(self.storage_path, LocalArtifact.INPUT_PARAMETERS)

    @property
    def data_file(self):
        return os.path.join(self.storage_path, LocalArtifact.DATA_FILE)

    @property
    def status_file(self):
        return os.path.join(self.storage_path, LocalArtifact.STATUS_FILE)

    @property
    def status(self):
        with open(self.status_file) as fp:
            return fp.read()

    def set_status(self, status):
        with open(self.status_file, 'w') as fp:
            fp.write(status)

    @property
    def metrics(self):
        metrics_dir = os.path.join(
            self.storage_path, LocalArtifact.METRICS_DIR)
        return [Metric(metric, os.path.join(metrics_dir, metric)) for metric in self.metric_names]

    @property
    def metric_names(self):
        metrics_dir = os.path.join(
            self.storage_path, LocalArtifact.METRICS_DIR)
        if os.path.isdir(metrics_dir):
            return os.listdir(metrics_dir)
        else:
            return []

    def metric(self, metric_name):
        metric_dir = os.path.join(
            self.storage_path, LocalArtifact.METRICS_DIR, metric_name)
        if os.path.exists(metric_dir):
            return Metric(metric_name, metric_dir)
        else:
            return None

    def create_metric(self, metric_name):
        metric_dir = os.path.join(
            self.storage_path, LocalArtifact.METRICS_DIR, metric_name)
        os.makedirs(metric_dir, exist_ok=True)
        return Metric(metric_name, metric_dir)


class ScalarMetricsLogger:

    def __init__(self, artifact, names):
        self.fp = {}
        self.names = names
        self.artifact = artifact

    def open(self):
        for name in self.names:
            metric_view = self.artifact.create_metric(
                name).create_view(MetricView.SCALAR_VIEW)
            self.fp[name] = open(metric_view.view_file, 'a')

    def log(self, name, step, value):
        self.fp[name].write("%f %f %f\n" %
                            (time.time(), float(step), float(value)))
        self.fp[name].flush()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        for fp in self.fp.values():
            fp.close()
