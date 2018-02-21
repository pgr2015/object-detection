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
import logging as log
import os
import shutil

from bonseyes.api import DataSet
from bonseyes_containers import tool_api
from bonseyes_containers.utils import load_callable
from bonseyes_training_base import BONSEYES_DATASET_TYPE


def process_data(artifact, input_data, input_files, processing_fun):

    processing_fun = load_callable(processing_fun)

    output_file = artifact.data_file

    log.info("Starting processing")

    input_artifact = input_data['input-url']

    data_set = DataSet(input_artifact)

    input_samples = data_set.samples.items()

    extra_params = {}
    extra_params.update(input_data)
    extra_params.update(input_files)
    del extra_params['name']
    del extra_params['input-url']

    samples = {}

    for sample_name, sample in input_samples:

        sample_dir = os.path.join(output_file, sample_name)
        os.makedirs(sample_dir)

        data_view_map = {}

        for data_view_type, data_view_fp in processing_fun(sample_name, sample, **extra_params):

            data_view_path = os.path.join(sample_dir, data_view_type)

            with open(data_view_path, 'wb') as fp:
                shutil.copyfileobj(data_view_fp, fp)

            data_view_fp.close()

            data_view_map[data_view_type] = os.path.join(
                sample_name, data_view_type)

        if len(data_view_map) == 0:
            continue

        samples[sample_name] = {'views': data_view_map,
                                'annotations': sample['annotations']}

    with open(os.path.join(output_file, 'dataset.json'), 'w') as fp:
        json.dump(samples, fp)

    log.info("Processing finished")


def create_processing_app(processing_function, description, extra_params=None):

    parameters = {'input-url': {'label': 'Input data set', 'type': 'artifact',
                                'artifact-type': BONSEYES_DATASET_TYPE}}

    if extra_params is not None:
        parameters.update(extra_params)

    extra_args = {'processing_fun': processing_function}

    app = tool_api.create_app(
        process_data, description, parameters, BONSEYES_DATASET_TYPE, extra_args)

    return app
