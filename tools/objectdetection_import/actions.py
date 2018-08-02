import os
import tarfile
import csv
from collections import OrderedDict

from PIL import Image
import xml.etree.ElementTree as ET

from bonseyes_objectdetection import BBOX_TYPE

from com_bonseyes_base.formats.data.dataset.api import DataSetEditor
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_training_base.lib import BONSEYES_PNG_IMAGE_TYPE, BONSEYES_JPEG_IMAGE_TYPE
from com_bonseyes_training_base.lib.import_helper import write_dataset


def get_data(images: str, labels: str, image_type: str):

    samples_names = {}

    if image_type is BONSEYES_PNG_IMAGE_TYPE:
        file_extension = '.png'
    else:
        file_extension = '.jpg'

    with tarfile.open(images, 'r') as tar:
        for member in tar.getmembers():

            file = member.name
            file = os.path.normpath(file)
            if not file.endswith(file_extension):
                continue
            #File name without extensions    
            sample_id = os.path.basename(file)[:-4]
            samples_names[sample_id] = member
            
        with tarfile.open(labels,'r') as tar_labels:
            file_names= tar_labels.getnames()
            for file_name in file_names:
                anno_xml=tar_labels.extractfile(file_name)
                tree = ET.parse(anno_xml)
                root = tree.getroot()
                size = root.find('size')
                width = int(size.find('width').text)
                height = int(size.find('height').text)
                depth = int(size.find('depth').text)
                objects = root.findall('object')
                if objects:
                    flag = 0
                    for n, j in enumerate(objects):
                        object_type = j.find('name').text
                        child = j.find('bndbox')
                        xmin = child.find('xmin').text
                        xmax = child.find('xmax').text
                        ymin = child.find('ymin').text
                        ymax = child.find('ymax').text
                frame_name = file_name[:-4]
                annotations = OrderedDict(
                                [('annotation',
                                  OrderedDict([('folder', '.'), ('filename', frame_name + '_data_' + image_type),
                                               ('path', frame_name + '_data_' + image_type),
                                               ('source', OrderedDict([('database', 'Bonseyes_OD')])),
                                               ('size', OrderedDict([('width', width), ('height', height),
                                                                     ('depth', '3')])),
                                               ('object', OrderedDict([('name', object_type),
                                                                       ('bndbox', OrderedDict(
                                                                           [('xmin', int(xmin)),
                                                                            ('xmax', int(xmax)),
                                                                            ('ymin', int(ymin)),
                                                                            ('ymax', int(ymax))
                                                                            ]))]))]))])
                img_name = frame_name+'.jpg'
                img = tar.extractfile(img_name)
                yield str(frame_name), {BONSEYES_PNG_IMAGE_TYPE: img}, {BBOX_TYPE: annotations}
        




def create(context: Context[DataSetEditor], images: str, labels: str, image_type: str ='JPG'):
    if image_type is 'PNG':
        image_type = BONSEYES_PNG_IMAGE_TYPE
    else:
        image_type = BONSEYES_JPEG_IMAGE_TYPE
    data = get_data(images, labels, image_type)
    write_dataset(context.data, data)

