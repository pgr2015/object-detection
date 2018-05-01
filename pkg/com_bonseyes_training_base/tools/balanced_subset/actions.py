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

import random

from collections import defaultdict

import logging

from bonseyes.tool.storage import Encoding
from bonseyes.tool_api import DataSet


def create(version, dataset, annotation, subset_name, size):

    samples = DataSet(dataset).samples

    # count the frequency of each class
    counts = defaultdict(lambda: 0)

    valid_samples = 0

    for sample in samples.values():
        sample_annotation = sample.get('annotations', {}).get(annotation, None)
        if sample_annotation is not None:
            counts[sample_annotation] += 1
            valid_samples += 1

    min_samples = min(counts.values())

    samples_per_class = valid_samples * float(size) / len(counts)

    if min_samples < samples_per_class:
        logging.error("Total samples: %d" % len(samples))
        logging.error("Samples of the rarest class: %d" % min_samples)
        logging.error("Required samples per class: %d" % samples_per_class)
        logging.error("Samples per class:")
        for name, value in counts.items():
            logging.error("  " + str(name) + ": " + str(value))

        raise Exception('There are not enough samples in one of the classes to build the subset')

    # samples that remain to be selected
    to_pick = {x: samples_per_class for x in counts}

    # pick elements for the validation set
    sample_names = list(samples.keys())
    random.shuffle(sample_names)

    output_samples = {}

    for sample_name in sample_names:

        sample = samples[sample_name]

        sample_annotation = sample.get('annotations', {}).get(annotation, None)

        # skip samples without annotation
        if sample_annotation is None:
            continue

        if to_pick[sample_annotation] > 0:
            output_samples[sample_name] = {'annotations': {subset_name: True}}
            to_pick[sample_annotation] -= 1

    output_dir = version.create_data_directory()
    output_dir.create_file('dataset_processing.json', output_samples, encoding=Encoding.JSON)

