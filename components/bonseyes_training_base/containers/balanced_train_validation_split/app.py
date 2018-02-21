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
import numpy
import os

from bonseyes_training_base.train_validation_split_container import create_train_validation_split_app


def split_indexes(output_tensor):

    # compute the number of samples in each class
    stats = [0] * 2

    for y_label in output_tensor:
        stats[numpy.argmax(y_label).astype(int)] += 1

    # we want class probability to be equally distributed in the validation set
    # and we want to take 10 % at most of the samples of each class for the validation
    # so we compute the number of elements to pick for the validation set to be
    # at most 10 % of the elements of the rarest class

    min_samples = int(min(stats) * 0.1)

    if min_samples < 1:
        raise Exception('There are not enough samples in one of the classes')

    to_pick = [min_samples] * 2

    logging.info("Counts per class: " + str(stats))
    logging.info("To pick : " + str(to_pick))

    train_indexes = []
    validation_indexes = []

    # pick elements from the two classes
    for idx, y_label in enumerate(output_tensor):
        if to_pick[numpy.argmax(y_label)] > 0:
            validation_indexes.append(idx)
            to_pick[numpy.argmax(y_label)] -= 1
        else:
            train_indexes.append(idx)

    return train_indexes, validation_indexes


DESCRIPTION = os.environ['TASK_LABEL'] + \
    ": Create the learning/ (balanced) validation split"

INPUT_TYPE = os.environ['TASK_PACKAGE'] + '.tensor'
OUTPUT_TYPE = os.environ['TASK_PACKAGE'] + '.training-set'


app = create_train_validation_split_app(
    split_indexes, DESCRIPTION, INPUT_TYPE, OUTPUT_TYPE)
