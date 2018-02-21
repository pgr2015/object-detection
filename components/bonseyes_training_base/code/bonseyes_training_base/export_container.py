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
import h5py
import logging
import numpy

from bonseyes.api import DataSet
from bonseyes_containers import tool_api
from bonseyes_containers.utils import load_callable
from bonseyes_training_base import BONSEYES_DATASET_TYPE

"""

Create a HDF5 file with two tensors suitable for training from an imported dataset. 

The 'input' dataset contains the input for the neural network, while the 'output' dataset contains the expected 
output of the network. It is possible to provide a function to filter which samples have to be included in the 
output. 

To use this call create_export_app to create the app in your app.py.

"""

INPUT_DATA_SET_NAME = 'input'
OUTPUT_DATA_SET_NAME = 'output'
SAMPLES_names_SET_NAME = 'sample_names'



def process_data(artifact, input_data, input_files,
                 filtering_fun, processing_fun,
                 input_type, output_type,
                 input_shape, output_shape):
    filtering_fun = load_callable(filtering_fun)
    processing_fun = load_callable(processing_fun)

    output_file = artifact.data_file

    log.info("Starting processing")

    input_artifact = input_data['input-url']

    data_set = DataSet(input_artifact)

    extra_params = {}
    extra_params.update(input_data)
    extra_params.update(input_files)
    del extra_params['name']
    del extra_params['input-url']

    samples = {key: value for key, value in data_set.samples.items(
    ) if filtering_fun(key, value, **extra_params)}

    with h5py.File(output_file, "w") as f:
        
        #input HDF5
        input_data_set = f.create_dataset(INPUT_DATA_SET_NAME,
                                          tuple([len(samples)] +
                                                list(input_shape)),
                                          dtype=input_type)

        if tuple(output_shape) == tuple([1]):
            logging.info('Creating a simple vector as output')
            full_output_shape = (len(samples), )
        else:
            full_output_shape = tuple([len(samples)] + list(output_shape))
            
        #output HDF5
        output_data_set = f.create_dataset(
            OUTPUT_DATA_SET_NAME, full_output_shape, dtype=output_type)

        #names images HDF5
        dt = h5py.special_dtype(vlen=numpy.unicode)
        sample_names = f.create_dataset(
            SAMPLES_names_SET_NAME, (len(samples),), dtype=dt)

        for i, (sample_name, sample) in enumerate(samples.items()):
            input_sample = numpy.zeros(input_shape, dtype=input_type)
            output_sample = numpy.zeros(output_shape, dtype=output_type)

            processing_fun(sample_name, sample, input_sample,
                           output_sample, **extra_params)

            input_data_set[i] = input_sample
            output_data_set[i] = output_sample
            sample_names[i] = sample_name

    log.info("Processing finished")


def create_export_app(filtering_function, processing_function, description, output_type,
                      input_shape, output_shape, input_data_type='f', output_data_type='f', extra_params=None):

    parameters = {'input-url': {'label': 'Input data set', 'type': 'artifact',
                                'artifact-type': BONSEYES_DATASET_TYPE}}

    extra_args = {'filtering_fun': filtering_function,
                  'processing_fun': processing_function,
                  'input_type': input_data_type,
                  'output_type': output_data_type,
                  'input_shape': input_shape,
                  'output_shape': output_shape}

    if extra_params is not None:
        parameters.update(extra_params)

    app = tool_api.create_app(
        process_data, description, parameters, output_type, extra_args)

    return app
