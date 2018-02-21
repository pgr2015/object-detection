#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import requests
from PIL import Image
from io import BytesIO
import numpy as np

import logging as log

from bonseyes_youtubebb import DIGIT_TYPE
from bonseyes_training_base import BONSEYES_PNG_IMAGE_TYPE


def filter_samples(sample_name, sample_data):
    return True


def export(sample_name, sample, input_sample, output_sample):

    image_url = sample['data'][BONSEYES_PNG_IMAGE_TYPE]

    ret = requests.get(image_url)

    if ret.status_code != 200:
        raise Exception("Unable to download %s (code: %d)" %
                        (image_url, ret.status_code))

    # create input tensor
    img = Image.open(BytesIO(ret.content))
    img = (img.resize((416, 416), Image.LANCZOS)).convert('RGB') 
    
    mean = (113, 115, 114)

    # subtract means per pixel
    pixels = np.array(img, dtype=np.float32)

    for x in range(img.size[1]):
        for y in range(img.size[0]):
            pixels[x,y] = np.subtract(pixels[x,y], mean)

    img = pixels / np.float32(256)
 
    # Swap.
    img = np.swapaxes(img, 1, 2)
    img = np.swapaxes(img, 0, 1)

    """

    Create a HDF5 file with two tensors suitable for training from an imported dataset. 
    
    The 'input' dataset contains the input for the neural network, while the 'output' dataset contains the expected 
    output of the network. It is possible to provide a function to filter which samples have to be included in the 
    output. 
    
    To use this call create_export_app to create the app in your app.py.
    
    """

    input_sample[:,:,:] = img[:,:,:]

    output_sample[:]=sample['annotations'][DIGIT_TYPE]




