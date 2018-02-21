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

import os
import tempfile
import h5py

import theano
import theano.tensor as theano_tensor
import lasagne
import numpy as np

import logging as log
import json

from bonseyes.api import Artifact
from bonseyes_mnist.architecture import build_mlp, iterate_minibatches


def load_dataset(url):

    with tempfile.TemporaryDirectory() as tmp_dir:

        input_file = os.path.join(tmp_dir, 'data.hdf5')

        log.info("Downloading %s to %s" % (url, input_file))
        with open(input_file, 'wb') as fp:
            Artifact(url).export(fp)
        log.info("Downloaded %d bytes", os.path.getsize(input_file))

        with h5py.File(input_file, "r") as data:
            return data['input'][:], np.int32(data['output'][:])


def load_model_weights(url):
    with tempfile.TemporaryDirectory() as tmp_dir:

        input_file = os.path.join(tmp_dir, 'model.npz')

        log.info("Downloading %s to %s" % (url, input_file))
        with open(input_file, 'wb') as fp:
            Artifact(url).export(fp)
        log.info("Downloaded %d bytes", os.path.getsize(input_file))

        with np.load(input_file) as f:
            param_values = [f['arr_%d' % i] for i in range(len(f.files))]

        return param_values


def perform_benchmark(artifact, input_data, input_files):

    model_url = input_data['model']
    tensor_url = input_data['tensor']

    log.info("Loading data...")

    x_test, y_test = load_dataset(tensor_url)

    log.info("Loading model...")

    param_values = load_model_weights(model_url)

    log.info("Building network...")

    input_var = theano_tensor.tensor4('inputs')
    target_var = theano_tensor.ivector('targets')

    network = build_mlp(input_var)

    test_prediction = lasagne.layers.get_output(network, deterministic=True)
    test_loss = lasagne.objectives.categorical_crossentropy(
        test_prediction, target_var)
    test_loss = test_loss.mean()

    test_acc = theano_tensor.mean(theano_tensor.eq(theano_tensor.argmax(test_prediction, axis=1), target_var),
                                  dtype=theano.config.floatX)

    val_fn = theano.function([input_var, target_var], [
                             test_loss, test_acc])

    lasagne.layers.set_all_param_values(network, param_values)

    log.info("Starting benchmarking...")

    val_err = 0
    val_acc = 0
    val_batches = 0
    for batch in iterate_minibatches(x_test, y_test, 500, shuffle=False):
        inputs, targets = batch
        err, acc = val_fn(inputs, targets)
        val_err += err
        val_acc += acc
        val_batches += 1

    log.info("Writing results...")

    with open(artifact.data_file, 'w') as fp:
        json.dump({'loss': val_err / val_batches,
                   'accuracy':  val_acc / val_batches * 100}, fp)
