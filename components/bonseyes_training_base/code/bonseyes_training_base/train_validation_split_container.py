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
import logging as log
import os
from tempfile import TemporaryDirectory

import h5py

from bonseyes.api import Artifact
from bonseyes_containers import tool_api
from bonseyes_containers.utils import load_callable
from bonseyes_training_base.export_container import OUTPUT_DATA_SET_NAME, INPUT_DATA_SET_NAME

TRAINING_GROUP_NAME = 'learning'
VALIDATION_GROUP_NAME = 'validation'


def process_data(artifact, input_data, input_files, split_indexes_fun):

    split_indexes_fun = load_callable(split_indexes_fun)

    output_file = artifact.data_file

    log.info("Starting processing")

    input_artifact = input_data['input-url']

    extra_params = {}
    extra_params.update(input_data)
    extra_params.update(input_files)
    del extra_params['name']
    del extra_params['input-url']

    with TemporaryDirectory() as tmp_dir:

        tensor_file = os.path.join(tmp_dir, 'merged_tensors')

        with open(tensor_file, 'wb') as fp:
            Artifact(input_artifact).export(fp)

        with h5py.File(tensor_file) as merged_tensors:

            learning_indexes, validation_indexes = split_indexes_fun(
                merged_tensors[OUTPUT_DATA_SET_NAME], **extra_params)

            if len(learning_indexes) == 0:
                raise Exception("Not enough learning samples")

            if len(validation_indexes) == 0:
                raise Exception("Not enough validation samples")

            with h5py.File(output_file, "w") as splitted_tensors:

                dest_val = splitted_tensors.create_group(VALIDATION_GROUP_NAME)
                dest_learn = splitted_tensors.create_group(TRAINING_GROUP_NAME)

                def copy_values(dest_group, dest_name, indexes, input_dataset):
                    new_shape = list(input_dataset.shape)
                    new_shape[0] = len(indexes)

                    dest_dset = dest_group.create_dataset(
                        dest_name, new_shape, dtype=input_dataset.dtype)
                    dest_dset[:] = input_dataset[indexes]
                    
                copy_values(dest_val, INPUT_DATA_SET_NAME,
                            validation_indexes, merged_tensors[INPUT_DATA_SET_NAME])
                copy_values(dest_learn, INPUT_DATA_SET_NAME,
                            learning_indexes, merged_tensors[INPUT_DATA_SET_NAME])

                copy_values(dest_val, OUTPUT_DATA_SET_NAME,
                            validation_indexes, merged_tensors[OUTPUT_DATA_SET_NAME])
                copy_values(dest_learn, OUTPUT_DATA_SET_NAME,
                            learning_indexes, merged_tensors[OUTPUT_DATA_SET_NAME])

    log.info("Processing finished")


def create_train_validation_split_app(split_indexes_fun, description, input_type, output_type, extra_params=None):

    parameters = {'input-url': {'label': 'Input tensor', 'type': 'artifact',
                                'artifact-type': input_type}}

    if extra_params is not None:
        parameters.update(extra_params)

    extra_args = {'split_indexes_fun': split_indexes_fun}

    return tool_api.create_app(process_data, description, parameters, output_type, extra_args)
