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
import os

import h5py

from bonseyes.training.base import DATA_TENSOR_INPUT_DATASET_NAME, \
    NORMALIZATION_PARAMS_MEAN_DATASET_NAME, NORMALIZATION_PARAMS_STD_DATASET_NAME, \
    DATA_TENSOR_SAMPLE_NAMES_DATASET_NAME, DATA_TENSOR_OUTPUT_DATASET_NAME


CHUNK_SIZE = os.environ.get("CHUNK_SIZE", 10000)


def process_input_dataset(input_file, output_file, mean, std):

    input_dataset = input_file[DATA_TENSOR_INPUT_DATASET_NAME]

    output_dataset = output_file.create_dataset(DATA_TENSOR_INPUT_DATASET_NAME,
                                                shape=input_dataset.shape,
                                                dtype='float32')

    sample_count = input_dataset.shape[0]

    for idx in range(0, sample_count, CHUNK_SIZE):
        import logging
        last_idx = min(idx + CHUNK_SIZE, sample_count)
        output_dataset[idx:last_idx, :, :] = (input_dataset[idx:last_idx] - mean) / std


def copy_dataset(input_file, output_file, dataset_name):

    input_dataset = input_file[dataset_name]

    output_dataset = output_file.create_dataset(dataset_name,
                                                shape=input_dataset.shape,
                                                dtype=input_dataset.dtype)

    sample_count = input_dataset.shape[0]

    for idx in range(0, sample_count, CHUNK_SIZE):
        last_idx = min(idx + CHUNK_SIZE, sample_count)
        output_dataset[idx:last_idx] = input_dataset[idx:last_idx]


def create(version, tensor, parameters):

    logging.info("Starting processing")

    with h5py.File(parameters, 'r') as f:
        mean = f[NORMALIZATION_PARAMS_MEAN_DATASET_NAME][:]
        std = f[NORMALIZATION_PARAMS_STD_DATASET_NAME][:]

    with version.edit_data_file() as output_file_path:

        with h5py.File(tensor, 'r') as input_file, \
             h5py.File(output_file_path, 'w') as output_file:

            logging.info("Copying ancillary datasets")

            for key in input_file.keys():
                if key != DATA_TENSOR_INPUT_DATASET_NAME:
                    copy_dataset(input_file, output_file, key)

            logging.info("Normalizing input datasets")
            process_input_dataset(input_file, output_file, mean, std)

    logging.info("Completed")

