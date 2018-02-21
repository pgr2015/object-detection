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
import time

import theano
import theano.tensor as theano_tensor
import lasagne
import numpy as np

import logging as log

from bonseyes.api import Artifact
from bonseyes_containers.local_artifacts import ScalarMetricsLogger
from bonseyes_mnist.architecture import build_mlp, build_cnn, iterate_minibatches
from bonseyes_training_base.export_container import INPUT_DATA_SET_NAME, OUTPUT_DATA_SET_NAME
from bonseyes_training_base.train_validation_split_container import TRAINING_GROUP_NAME, VALIDATION_GROUP_NAME


def load_dataset(url):
    with tempfile.TemporaryDirectory() as tmp_dir:

        input_file = os.path.join(tmp_dir, 'training.dat')

        log.info("Downloading %s to %s" % (url, input_file))

        with open(input_file, 'wb') as fp:
            Artifact(url).export(fp)

        log.info("Downloaded %d bytes", os.path.getsize(input_file))

        data = h5py.File(input_file, "r")

        x_train = data[TRAINING_GROUP_NAME][INPUT_DATA_SET_NAME][:]
        x_val = data[VALIDATION_GROUP_NAME][INPUT_DATA_SET_NAME][:]

        y_train = data[TRAINING_GROUP_NAME][OUTPUT_DATA_SET_NAME][:]
        y_val = data[VALIDATION_GROUP_NAME][OUTPUT_DATA_SET_NAME][:]
        try:
            return x_train, np.int32(y_train), x_val, np.int32(y_val)
        except ValueError:
            return x_train, y_train, x_val, y_val


def perform_training(artifact, input_data, input_files):

    training_set_url = input_data['training-set']

    log.info("Loading data...")

    x_train, y_train, x_val, y_val = load_dataset(training_set_url)

    log.info("Building network...")

    input_var = theano_tensor.tensor4('inputs')
    target_var = theano_tensor.ivector('targets')

    network = build_cnn(input_var)

    prediction = lasagne.layers.get_output(network)
    loss = lasagne.objectives.categorical_crossentropy(
        prediction, target_var)
    loss = loss.mean()

    params = lasagne.layers.get_all_params(network, trainable=True)
    updates = lasagne.updates.nesterov_momentum(
        loss, params, learning_rate=0.01, momentum=0.9)

    test_prediction = lasagne.layers.get_output(
        network, deterministic=True)
    test_loss = lasagne.objectives.categorical_crossentropy(test_prediction,
                                                            target_var)
    test_loss = test_loss.mean()

    test_acc = theano_tensor.mean(theano_tensor.eq(theano_tensor.argmax(test_prediction, axis=1), target_var),
                                  dtype=theano.config.floatX)

    train_fn = theano.function(
        [input_var, target_var], loss, updates=updates)
    val_fn = theano.function([input_var, target_var], [
                             test_loss, test_acc])

    log.info("Starting training...")

    num_epochs = 10

    with ScalarMetricsLogger(artifact, ['train_loss', 'val_loss', 'val_acc']) as logger:

        # We iterate over epochs:
        for epoch in range(num_epochs):
            # In each epoch, we do a full pass over the training data:
            train_err = 0
            train_batches = 0
            start_time = time.time()
            for batch in iterate_minibatches(x_train, y_train, 500, shuffle=True):
                inputs, targets = batch
                train_err += train_fn(inputs, targets)
                train_batches += 1

            # And a full pass over the validation data:
            val_err = 0
            val_acc = 0
            val_batches = 0
            for batch in iterate_minibatches(x_val, y_val, 500, shuffle=False):
                inputs, targets = batch
                err, acc = val_fn(inputs, targets)
                val_err += err
                val_acc += acc
                val_batches += 1

            logger.log('train_loss', epoch, train_err / train_batches)
            logger.log('val_loss', epoch, val_err / val_batches)
            logger.log('val_acc', epoch, val_acc)

            # Then we print the results for this epoch:
            log.info("Epoch {} of {} took {:.3f}s\n".format(
                epoch + 1, num_epochs, time.time() - start_time))
            log.info("  training loss:\t\t{:.6f}\n".format(
                train_err / train_batches))
            log.info("  validation loss:\t\t{:.6f}\n".format(
                val_err / val_batches))
            log.info("  validation accuracy:\t\t{:.2f} %\n".format(
                val_acc / val_batches * 100))

        with open(artifact.data_file, 'wb') as fp:
            np.savez(fp, *lasagne.layers.get_all_param_values(network))
