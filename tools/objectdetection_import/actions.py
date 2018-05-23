#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import os
import tarfile
import csv
from collections import OrderedDict

from PIL import Image

import logging as log

from bonseyes_youtubebb import BONSEYES_OD_ANNOTATION_TYPE

from com_bonseyes_base.formats.data.dataset.api import DataSetEditor
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_training_base.lib import BONSEYES_PNG_IMAGE_TYPE, BONSEYES_JPEG_IMAGE_TYPE
from com_bonseyes_training_base.lib.import_helper import write_dataset


def get_data(images: str, labels: str, image_type: str):

    samples_names = {}

    if image_type is BONSEYES_PNG_IMAGE_TYPE:
        file_extension = '.png'
    else:
        file_extension = '.jpeg'

    with tarfile.open(images, 'r') as tar:
        for member in tar.getmembers():

            file = member.name
            file = os.path.normpath(file)

            if not file.endswith(file_extension):
                continue

            # File name without extension
            sample_id = os.path.basename(file)[:-4]

            samples_names[sample_id] = member

        with open(labels, 'r') as csv_file:

            reader = csv.reader(csv_file)
            previous_video = str('')
            second = 0

            for row in reader:
                video_id = row[0] + '+' + row[2] + '+' + row[4]

                if video_id != previous_video:
                    second = 0

                if row[5] == 'present':

                    # File name without extension
                    frame_name = 'frame_' + row[0] + '_' + row[2] + '_' + row[4] + '_' + str(second)

                    if frame_name in samples_names:
                        log.info('IN')

                        # Get image size
                        with Image.open(tar.extractfile(samples_names[frame_name])) as pil_image:
                            img_size = pil_image.size

                        # Extract the file in memory
                        img = tar.extractfile(samples_names[frame_name])

                        bounding_box = [float(row[6]), float(row[7]), float(row[8]), float(row[9])]
                        object_type = row[3]  # String

                        annotations = OrderedDict(
                            [('annotation',
                              OrderedDict([('folder', '.'), ('filename', frame_name + image_type),
                                           ('path', frame_name + image_type),
                                           ('source', OrderedDict([('database', 'Bonseyes_OD')])),
                                           ('size', OrderedDict([('width', img_size[0]), ('height', img_size[1]),
                                                                 ('depth', '3')])),
                                           ('segmented', '0'),
                                           ('object', OrderedDict([('name', object_type),
                                                                   ('pose', 'Frontal'),
                                                                   ('truncated', '0'),
                                                                   ('difficult', '0'),
                                                                   ('occluded', '0'),
                                                                   (
                                                                   'bndbox', OrderedDict([('xmin', bounding_box[0]),
                                                                                          ('xmax', bounding_box[1]),
                                                                                          ('ymin', bounding_box[2]),
                                                                                          ('ymax', bounding_box[
                                                                                              3])]))]))]))])


                        yield str(frame_name), {BONSEYES_PNG_IMAGE_TYPE: img}, {
                            BONSEYES_OD_ANNOTATION_TYPE: annotations}

                second += 1
                previous_video = video_id


def create(context: Context[DataSetEditor], images: str, labels: str, image_type: str ='PNG'):
    if image_type is 'PNG':
        image_type = BONSEYES_PNG_IMAGE_TYPE
    else:
        image_type = BONSEYES_JPEG_IMAGE_TYPE
    data = get_data(images, labels, image_type)
    write_dataset(context.data, data)
