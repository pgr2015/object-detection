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

import h5py
import numpy as np
import logging as log
import caffe
import sys


def perform_benchmark(proto_path, weights_path, data_set, output_path):

    log.info("Loading data...")

    with h5py.File(data_set, "r") as data:
        x_test = data['input'][:]
        sample_names = data['sample_names'][:]

    log.info("Loading model...")

    net = caffe.Net(proto_path, weights_path, caffe.TEST)

    if len(net.inputs) > 1:
        raise Exception("Networks with more than one input layer are not supported")

    if len(net.outputs) > 1:
        raise Exception("Networks with more than one output layer are not supported")

    sample_count = x_test.shape[0]

    if sample_count == 0:
        raise Exception('No data was provided')

    inference_results = []

    log.info("Starting inference...")

    for i in range(sample_count):

        log.info("Computing inference for sample %d" % i)

        # load the sample in the network
        net.blobs[net.inputs[0]].data[...] = x_test[i]

        # perform the prediction
        predictions = net.forward()

        # save the inference results
        inference_results.append(np.copy(predictions[net.outputs[0]]))

    log.info("Writing results...")

    # create a matrix that can store the results
    output_shape = [sample_count] + list(inference_results[0].shape)
    output_tensor = np.zeros(shape=output_shape)

    # copy the results in the matrix
    for i in range(len(inference_results)):
        output_tensor[i] = inference_results[i]

    # save the result to the output file
    with h5py.File(output_path, 'w') as out_file:
        out_file.create_dataset('preds', data=inference_results)
        out_file.create_dataset('sample_names', data=sample_names)


if __name__ == "__main__":
    perform_benchmark(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
