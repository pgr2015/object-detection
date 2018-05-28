#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import zipfile

from bonseyes_objectdetection import BBOX_TYPE, WIDTH, HEIGHT

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

        # Check if images are in PNG or JPEG
        image_type = BONSEYES_PNG_IMAGE_TYPE
        encode_type = 'png'
        output_format = 'PNG'
        try:
            raw_dataset.samples.all[0].data.get(BONSEYES_PNG_IMAGE_TYPE).value.get()
        except KeyError:
            image_type = BONSEYES_JPEG_IMAGE_TYPE
            encode_type = 'jpg'
            output_format = 'JPEG'

        with open(list_file, 'w') as list_f:
            for sample in raw_dataset.samples.all:
                # Image
                image = Image.open(BytesIO(sample.data.get(image_type).value.get()))
                image.save(os.path.join(root_directory, sample.name + '_data_' + image_type), output_format)
                # Annotation
                annotation = sample.data.get(BBOX_TYPE).value.get()
                xml = convert_to_xml(annotation, root_directory)
                with open(os.path.join(root_directory, sample.name + '.xml'), 'w') as xml_file:
                    xml_file.write(ET.tostring(xml).decode("utf-8"))
                # Add it to the list
                list_f.write(os.path.join(sample.name + '_data_' + image_type) + ' ' +
                             os.path.join(sample.name + '.xml') + '\n')

        # Create the lmdb
        execute_with_logs('python3', '/opt/caffe/scripts/create_annoset.py',
                          '--anno-type=detection',
                          '--label-map-file=' + label_map,
                          '--min-dim=0',
                          '--max-dim=0',
                          '--resize-width=' + str(WIDTH),
                          '--resize-height=' + str(HEIGHT),
                          '--check-label',
                          '--encode-type=' + encode_type,
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


def convert_to_xml(annotation, root_directory):

    # Ensure XML elements order. Otherwise Caffe may fail loading annotations
    # VOC2012 actions and points are not supported

    annotation_element = ET.Element('annotation')

    folder_element = ET.SubElement(annotation_element, 'folder')
    folder_element.text = root_directory

    filename_element = ET.SubElement(annotation_element, 'filename')
    filename_element.text = annotation['annotation']['filename']

    if 'path' in annotation['annotation']:
        path_element = ET.SubElement(annotation_element, 'path')
        path_element.text = annotation['annotation']['path']

    if 'source' in annotation['annotation']:
        source_element = ET.SubElement(annotation_element, 'source')
        if 'database' in annotation['annotation']['source']:
            source_database_element = ET.SubElement(source_element, 'database')
            source_database_element.text = annotation['annotation']['source']['database']
        if 'annotation' in annotation['annotation']['source']:
            source_annotation_element = ET.SubElement(source_element, 'annotation')
            source_annotation_element.text = annotation['annotation']['source']['annotation']
        if 'image' in annotation['annotation']['source']:
            source_image_element = ET.SubElement(source_element, 'image')
            source_image_element.text = annotation['annotation']['source']['image']

    size_element = ET.SubElement(annotation_element, 'size')
    width_element = ET.SubElement(size_element, 'width')
    width_element.text = str(annotation['annotation']['size']['width'])
    height_element = ET.SubElement(size_element, 'height')
    height_element.text = str(annotation['annotation']['size']['height'])
    depth_element = ET.SubElement(size_element, 'depth')
    depth_element.text = str(annotation['annotation']['size']['depth'])

    if 'segmented' in annotation['annotation']:
        segmented_element = ET.SubElement(annotation_element, 'segmented')
        segmented_element.text = annotation['annotation']['segmented']

    if type(annotation['annotation']['object']) is not list:
        annotated_objects = [annotation['annotation']['object']]
        annotation['annotation']['object'] = annotated_objects
    else:
        annotated_objects = annotation['annotation']['object']

    for annotated_object in annotated_objects:

        object_element = ET.SubElement(annotation_element, 'object')

        object_name_element = ET.SubElement(object_element, 'name')
        object_name_element.text = annotated_object['name']

        if 'pose' in annotated_object:
            pose_element = ET.SubElement(object_element, 'pose')
            pose_element.text = annotated_object['pose']

        if 'truncated' in annotated_object:
            truncated_element = ET.SubElement(object_element, 'truncated')
            truncated_element.text = annotated_object['truncated']

        if 'occluded' in annotated_object:
            occluded_element = ET.SubElement(object_element, 'occluded')
            occluded_element.text = annotated_object['occluded']

        if 'difficult' in annotated_object:
            difficult_element = ET.SubElement(object_element, 'difficult')
            difficult_element.text = annotated_object['difficult']

        bndbox_element = ET.SubElement(object_element, 'bndbox')

        xmin_element = ET.SubElement(bndbox_element, 'xmin')
        xmin_element.text = str(annotated_object['bndbox']['xmin'])
        ymin_element = ET.SubElement(bndbox_element, 'ymin')
        ymin_element.text = str(annotated_object['bndbox']['ymin'])
        xmax_element = ET.SubElement(bndbox_element, 'xmax')
        xmax_element.text = str(annotated_object['bndbox']['xmax'])
        ymax_element = ET.SubElement(bndbox_element, 'ymax')
        ymax_element.text = str(annotated_object['bndbox']['ymax'])

        if 'part' in annotated_object:

            if type(annotated_object['part']) is not list:
                object_parts = [annotated_object['part']]
                annotated_object['part'] = object_parts
            else:
                object_parts = annotated_object['part']

            for part in object_parts:

                part_element = ET.SubElement(object_element, 'part')

                part_name_element = ET.SubElement(part_element, 'name')
                part_name_element.text = part['name']

                part_bndbox_element = ET.SubElement(part_element, 'bndbox')

                part_xmin_element = ET.SubElement(part_bndbox_element, 'xmin')
                part_xmin_element.text = str(part['bndbox']['xmin'])
                part_ymin_element = ET.SubElement(part_bndbox_element, 'ymin')
                part_ymin_element.text = str(part['bndbox']['ymin'])
                part_xmax_element = ET.SubElement(part_bndbox_element, 'xmax')
                part_xmax_element.text = str(part['bndbox']['xmax'])
                part_ymax_element = ET.SubElement(part_bndbox_element, 'ymax')
                part_ymax_element.text = str(part['bndbox']['ymax'])

    return annotation_element
