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
import cv2

from io import BytesIO

from bonseyes.training.base import BONSEYES_JPEG_IMAGE_TYPE, \
                                   BONSEYES_PNG_IMAGE_TYPE, \
                                   BONSEYES_TIFF_IMAGE_TYPE
from bonseyes.training.base.dataset_parallelize_process import read_datasets_and_process_samples
from bonseyes.training.base.import_helper import write_dataset

from augmentation_preprocessing import augment_image


def process_data(augmentation_size, seed, export_augmented, enable_tan_trigg,
                 dataset_id, sample_name, sample, data, output_queue):

    nparr = numpy.fromstring(data, numpy.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    (images_aug, images_tt) = augment_image(img_np, augmentation_size, enable_tan_trigg, seed)

    data_outs = []

    if export_augmented:

        for index, img in enumerate(images_aug):

            ret, data_out = cv2.imencode(".jpg", img)
            if not ret:
                logging.info("Failed to decode an augmented image (" + str(index) + ")from " + sample_name)
                return

            data_outs.append((sample_name + "_aug_" + str(index), data_out))

    if enable_tan_trigg:

        for index, img in enumerate(images_tt):

            ret, data_out = cv2.imencode(".jpg", img)
            if not ret:
                logging.info("Failed to decode an tan trigg image (" + str(index) + ")from " + sample_name)
                return

            data_outs.append((sample_name + "_tt_" + str(index), data_out))

    # Add original image
    results = sample, data
    output_queue.put([dataset_id, sample_name, results])

    # Add augmented images
    for aug_sample_name, data_out in data_outs:
        results = sample, data_out
        output_queue.put([dataset_id, aug_sample_name, results])


def write_data(version, output_queue, total_samples):

    logging.info("Start to write augmented data")

    def get_output_data():

        skipped = 0

        while True:

            next_item = output_queue.get()

            if next_item is None:
                break

            dataset_id, sample_name, results = next_item

            if results is None:
                skipped += 1
                continue

            if dataset_id is None:
                sample_id = sample_name
            else:
                sample_id = str(dataset_id) + "." + sample_name

            sample = results[0]
            data = results[1]

            data_type = BONSEYES_JPEG_IMAGE_TYPE
            sample_data = {data_type: BytesIO(data)}

            sample_annotations = {}
            if 'annotations' in sample:
                sample_annotations = sample['annotations']

            yield [sample_id, sample_data, sample_annotations]

        if skipped > 0:
            logging.info("Skipped: " + str(skipped))

    write_dataset(version, get_output_data())

    logging.info("Finished to write augmented data")


def create(version, datasets, augmentation_size, seed,
           export_augmented=True, enable_tan_trigg=False):

    logging.getLogger("urllib3").setLevel(logging.WARNING)

    data_names = [BONSEYES_JPEG_IMAGE_TYPE, BONSEYES_PNG_IMAGE_TYPE, BONSEYES_TIFF_IMAGE_TYPE]

    def bound_processing_fun(*args):
        process_data(int(augmentation_size), int(seed), bool(export_augmented), bool(enable_tan_trigg), *args)

    def bound_write_fun(*args):
        write_data(version, *args)

    read_datasets_and_process_samples(datasets,
                                      'data', data_names,
                                      2, bound_processing_fun,
                                      bound_write_fun)
