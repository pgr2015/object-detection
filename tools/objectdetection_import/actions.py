#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import os
import tempfile
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
    samples_names = []
    if image_type is BONSEYES_PNG_IMAGE_TYPE:
        file_extension = '.png'
    else:
        file_extension = '.jpeg'

    with tempfile.TemporaryDirectory() as tmp_dir:
        with tarfile.open(images, 'r') as tar:
            for member in tar.getmembers():

                file = member.name
                file = os.path.normpath(file)

                if not file.endswith(file_extension):
                    continue

                sample_id = os.path.basename(file)[:-4]

                member.name = os.path.join(*(member.name.split(os.path.sep)[1:]))

                samples_names.append(sample_id)
                tar.extract(member, tmp_dir)

        with open(labels, 'r') as csv_file:

            reader = csv.reader(csv_file)
            previous_video = str('')
            second = 0

            for row in reader:
                video_id = row[0] + '+' + row[2] + '+' + row[4]

                if video_id != previous_video:
                    second = 0

                if row[5] == 'present':
                    frame_path = os.path.join(tmp_dir)
                    frame_path = os.path.join(frame_path, 'frame_' + row[0] + '_' + row[2] + '_' + row[4] + '_' + str(
                        second) + file_extension)

                    frame_name = 'frame_' + row[0] + '_' + row[2] + '_' + row[4] + '_' + str(second) + file_extension
                    frame_name = frame_name[:-4]

                    try:
                        if os.path.isfile(frame_path):
                            log.info('frame_path:')
                            log.info(frame_path)

                            img = Image.open(frame_path)

                            bounding_box = [float(row[6]), float(row[7]), float(row[8]), float(row[9])]
                            object_type = row[3]

                            annotations = OrderedDict(
                                [('annotation',
                                  OrderedDict([('folder', '.'), ('filename', sample_id+image_type),
                                               ('path', './' + sample_id),
                                               ('source', OrderedDict([('database', 'Bonseyes_OD')])),
                                               ('size', OrderedDict([('width', img.size[0]), ('height', img.size[0]),
                                                                     ('depth', '3')])),
                                               ('segmented', '0'),
                                               ('object', OrderedDict([('name', object_type),
                                                                       ('pose', 'Frontal'),
                                                                       ('truncated', '0'),
                                                                       ('difficult', '0'),
                                                                       ('occluded', '0'),
                                                                       ('bndbox', OrderedDict([('xmin', bounding_box[0]),
                                                                                               ('xmax', bounding_box[1]),
                                                                                               ('ymin', bounding_box[2]),
                                                                                               ('ymax', bounding_box[3])]))]))]))])

                            sample_id = frame_name

                            yield str(sample_id), {BONSEYES_PNG_IMAGE_TYPE: img}, {BONSEYES_OD_ANNOTATION_TYPE: annotations}

                    except:
                        log.info("Missing video")

                second += 1
                previous_video = video_id


def create(context: Context[DataSetEditor], images: str, labels: str, image_type: str ='PNG'):
    if image_type is 'PNG':
        image_type = BONSEYES_PNG_IMAGE_TYPE
    else:
        image_type = BONSEYES_JPEG_IMAGE_TYPE
    data = get_data(images, labels, image_type)
    write_dataset(context.data, data)
