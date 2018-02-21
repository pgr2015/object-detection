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
import requests

from bonseyes.api import DataSet
from bonseyes_containers import tool_api
from bonseyes_containers.utils import load_callable
from bonseyes_training_base import BONSEYES_DATASET_TYPE


def process_data(artifact, input_data, input_files, sampling_fun):

    sampling_fun = load_callable(sampling_fun)

    output_file = artifact.data_file

    log.info("Starting processing")

    input_artifact = input_data['input-url']

    data_set = DataSet(input_artifact)

    extra_params = {}
    extra_params.update(input_data)
    extra_params.update(input_files)
    del extra_params['name']
    del extra_params['input-url']

    subset = sampling_fun(data_set.samples, **extra_params)

    output_samples = {}

    for sample_name, sample in subset.items():

        sample_dir = os.path.join(output_file, sample_name)
        os.makedirs(sample_dir)

        new_sample = {}

        for data_type in ['views', 'data']:

            if data_type not in sample:
                continue

            new_sample[data_type] = {}

            for entry_type, raw_url in sample[data_type].items():

                ret = requests.get(raw_url)

                if ret.status_code != 200:
                    raise Exception("Unable to download %s (code: %d)" % (
                        raw_url, ret.status_code))

                data_view_path = os.path.join(sample_dir, entry_type)

                with open(data_view_path, 'wb') as out_fp:
                    for chunk in ret.iter_content(chunk_size=1024):
                        if chunk:
                            out_fp.write(chunk)

                new_sample[data_type][entry_type] = os.path.join(
                    sample_name, entry_type)

        new_sample['annotations'] = sample['annotations']

        output_samples[sample_name] = new_sample

    with open(os.path.join(output_file, 'dataset.json'), 'w') as fp:
        json.dump(output_samples, fp)

    log.info("Processing finished")


def create_sampling_app(sampling_fun, description, extra_params=None):

    parameters = {'input-url': {'label': 'Input data set', 'type': 'artifact',
                                'artifact-type': BONSEYES_DATASET_TYPE}}

    if extra_params is not None:
        parameters.update(extra_params)

    extra_args = {'sampling_fun': sampling_fun}

    app = tool_api.create_app(
        process_data, description, parameters, BONSEYES_DATASET_TYPE, extra_args)

    return app
