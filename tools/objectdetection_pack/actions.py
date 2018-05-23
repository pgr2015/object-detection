#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import zipfile

from bonseyes_youtubebb import BONSEYES_OD_ANNOTATION_TYPE
from com_bonseyes_base.formats.data.data_tensors.api import DataTensorsEditor
from com_bonseyes_base.formats.data.dataset.api import DataSetViewer
from com_bonseyes_base.lib.api.tool import Context

from PIL import Image
from io import BytesIO
import tempfile
import logging as log
import os

import xml.etree.ElementTree as ET

from com_bonseyes_training_base.lib import BONSEYES_PNG_IMAGE_TYPE, BONSEYES_JPEG_IMAGE_TYPE
from com_bonseyes_base.lib.impl.utils import execute_with_logs


def create(context: Context[DataTensorsEditor], raw_dataset: DataSetViewer, label_map: str):

    with tempfile.TemporaryDirectory() as tmp_dir:

        database_name = 'Bonseyes_OD'
        root_directory = os.path.join(tmp_dir, database_name)
        os.mkdir(root_directory)

        output_dir = os.path.join(tmp_dir, database_name + '_lmdb')
        list_file = os.path.join(tmp_dir, 'lmdb.txt')
        link_dir = os.path.join(tmp_dir, 'link')

        with open(list_file, 'w') as list_f:
            for sample in raw_dataset.samples.all:
                image = Image.open(BytesIO(sample.data.get(BONSEYES_PNG_IMAGE_TYPE).value.get()))
                image.save(os.path.join(root_directory, sample.name + '_data_' + BONSEYES_PNG_IMAGE_TYPE), 'JPEG')

                annotation = sample.data.get(BONSEYES_OD_ANNOTATION_TYPE).value.get()

                with open(os.path.join(root_directory, sample.name + '.xml'), 'w') as xml_file:
                    annotation_element = ET.Element('annotation')
                    folder_element = ET.SubElement(annotation_element, 'folder')
                    folder_element.text = root_directory
                    filename_element = ET.SubElement(annotation_element, 'filename')
                    filename_element.text = annotation['annotation']['filename']
                    size_element = ET.SubElement(annotation_element, 'size')
                    width_element = ET.SubElement(size_element, 'width')
                    width_element.text = str(annotation['annotation']['size']['width'])
                    height_element = ET.SubElement(size_element, 'height')
                    height_element.text = str(annotation['annotation']['size']['height'])
                    depth_element = ET.SubElement(size_element, 'depth')
                    depth_element.text = str(annotation['annotation']['size']['depth'])

                    object_element = ET.SubElement(annotation_element, 'object')
                    name_element = ET.SubElement(object_element, 'name')
                    name_element.text = annotation['annotation']['object']['name']
                    bndbox_element = ET.SubElement(object_element, 'bndbox')
                    xmin_element = ET.SubElement(bndbox_element, 'xmin')
                    ymin_element = ET.SubElement(bndbox_element, 'ymin')
                    xmax_element = ET.SubElement(bndbox_element, 'xmax')
                    ymax_element = ET.SubElement(bndbox_element, 'ymax')
                    xmin_element.text = str(annotation['annotation']['object']['bndbox']['xmin'])
                    ymin_element.text = str(annotation['annotation']['object']['bndbox']['ymin'])
                    xmax_element.text = str(annotation['annotation']['object']['bndbox']['xmax'])
                    ymax_element.text = str(annotation['annotation']['object']['bndbox']['ymax'])

                    xml_file.write(ET.tostring(annotation_element).decode("utf-8"))
                    list_f.write(os.path.join(sample.name + '_data_' + BONSEYES_PNG_IMAGE_TYPE) + ' ' +
                                 os.path.join(sample.name + '.xml' + '\n'))

        execute_with_logs('python3', '/opt/caffe/scripts/create_annoset.py',
                          '--anno-type=detection',
                          '--label-map-file=' + label_map,
                          '--min-dim=0',
                          '--max-dim=0',
                          '--resize-width=300',
                          '--resize-height=300',
                          '--check-label',
                          '--encode-type=png',
                          '--encoded',
                          root_directory,
                          list_file,
                          output_dir,
                          link_dir)

        with context.data.edit_content() as output_file:
            with zipfile.ZipFile(output_file, 'a') as z:
                z.write(os.path.join(output_dir, 'data.mdb'), arcname='data.mdb')
                z.write(os.path.join(output_dir, 'lock.mdb'), arcname='lock.mdb')

    log.info('Processing finished')
