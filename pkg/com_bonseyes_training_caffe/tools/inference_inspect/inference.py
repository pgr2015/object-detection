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
        x_test = data['input'][0]

    log.info("Loading data...")

    log.info("Loading model...")
    log.info(x_test.shape)

    net = caffe.Net(proto_path, weights_path, caffe.TEST)
    log.info("Loading data...")

    sample_count = 1
    log.info("Loading data...")

    if sample_count == 0:
        raise Exception('No data was provided')
    log.info("Loading data...")

    inference_results = []

    log.info("Starting inference...")

    f = h5py.File(output_path, 'w')
    sbgrp = f.create_group("lyr")

    for i in range(sample_count):

        log.info("Computing inference for sample %d" % i)

        net.blobs[net.inputs[0]].data[...] = np.expand_dims(x_test, axis=0)

        # perform the prediction
        predictions = net.forward()



        # save the inference results
        inference_results.append(np.copy(predictions[net.outputs[0]]))
        i = 0
        for layer in net.blobs.keys():
            sbsbgrp = sbgrp.create_group(str(i))
            # if i==0:
            #    sbsbgrp.create_dataset("input",data=f['input'][0])
            sbsbgrp.create_dataset("output", data=net.blobs[layer].data)
            sbsbgrp.attrs['Name'] = layer
            sbsbgrp.attrs['DataType'] = 9
            log.info(net.blobs[layer].data.shape)
            i += 1
        f.close()

    log.info("Writing results...")

    # create a matrix that can store the results
    output_shape = [sample_count] + list(inference_results[0].shape)
    output_tensor = np.zeros(shape=output_shape)

    # copy the results in the matrix
    for i in range(len(inference_results)):
        output_tensor[i] = inference_results[i]


if __name__ == "__main__":
    perform_benchmark(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
