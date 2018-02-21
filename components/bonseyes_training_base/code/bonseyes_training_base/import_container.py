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

import requests

from bonseyes_containers import tool_api
from bonseyes_containers.utils import load_callable
from bonseyes_training_base import BONSEYES_DATASET_TYPE


def process_data(artifact, input_data, input_files, data_fun):

    data_fun = load_callable(data_fun)

    samples = {}

    params = {}
    params.update(input_data)
    params.update(input_files)
    del params['name']

    # write out the data and annotations
    log.info('Importing data and annotations')

    os.makedirs(artifact.data_file)

    for sample_name, data, annotations in data_fun(**params):

        sample_path = os.path.join(artifact.data_file, sample_name)
        

        try:
            os.makedirs(sample_path)
    
            data_map = {}
    
            for data_type, data_fp in data.items():
                data_path = os.path.join(sample_path, data_type)
    
                log.info(data_path)
                with open(data_path, 'wb') as fp:
 
                    shutil.copyfileobj(data_fp, fp)
                    
                    
                data_fp.close()
    
                data_map[data_type] = os.path.join(sample_name, data_type)
    
            samples[sample_name] = {'data': data_map}
    
            if sample_name not in samples:
                raise Exception("Cannot import annotations for sample " +
                                sample_name + " that has no data")
        except FileExistsError:
            log.info('Duplicated image. Added only the new label.')

        samples[sample_name]['annotations'] = annotations

    with open(os.path.join(artifact.data_file, 'dataset.json'), 'w') as fp:
        json.dump(samples, fp)

    log.info('Import process finished')


DEFAULT_PARAMS = {'input_file': {'type': 'file', 'label': "Input file"}}


def create_import_app(data_function, description, parameters=DEFAULT_PARAMS):

    extra_args = {'data_fun': data_function}

    app = tool_api.create_app(
        process_data, description, parameters, BONSEYES_DATASET_TYPE, extra_args)

    return app
