#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#

from com_bonseyes_base.formats.data.data_tensors.api import DataTensorsEditor, DimensionNames
from com_bonseyes_base.formats.data.database.api import DataType
from com_bonseyes_base.formats.data.dataset.api import DataSetViewer
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_training_base.lib import BONSEYES_PNG_IMAGE_TYPE
from com_bonseyes_training_base.lib.export_helper import write_classification_tensor

from PIL import Image
from io import BytesIO
import numpy as np

from bonseyes_youtubebb import DIGIT_TYPE
from com_bonseyes_base.formats.data.dataset.api import Datum

import requests
import subprocess
import sys
import os
import xml.etree.ElementTree as ET
import lxml.etree as etree

import logging as log


def _export_face(datum: Datum):
    # create input tensor
    
    
    img = Image.open(BytesIO(datum.value.get()))

    if img.size[0] != 300 and img.size[1] != 300:
        img = (img.resize((300, 300), Image.LANCZOS)).convert('RGB')
    else:
        img = img.convert('RGB')

    img = np.array(img)

    label = np.array([datum.sample.data.get(DIGIT_TYPE).value.get()])

    return img, label


def create(context: Context[DataTensorsEditor], raw_dataset: DataSetViewer):

    # find all the class names
    class_names = set()

    for sample in raw_dataset.samples.all:
        class_names.add(str(sample.data.get(DIGIT_TYPE).value.get()))

    class_names = list(class_names)

    # write out the input and output tensors
    write_classification_tensor(context,raw_dataset,
                                input_dimensions=[(DimensionNames.CHANNEL, 3),
                                                  (DimensionNames.HEIGHT, 300),
                                                  (DimensionNames.WIDTH, 300)],
                                input_type=DataType.UINT32,
                                class_names=class_names,
                                export_data_types=[BONSEYES_PNG_IMAGE_TYPE],
                                process_sample_fun=_export_face,
                                editor=context.data,
                                output_dimensions=[(DimensionNames.CLASS_INDEX, 5)],
                                output_type=DataType.UINT32)

    