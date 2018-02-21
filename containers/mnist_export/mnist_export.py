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
import requests
from PIL import Image
from io import BytesIO
import numpy as np

from bonseyes_mnist import DIGIT_TYPE
from bonseyes_training_base import BONSEYES_PNG_IMAGE_TYPE


def filter_samples(sample_name, sample_data):
    return True


def export(sample_name, sample, input_sample, output_sample):

    image_url = sample['data'][BONSEYES_PNG_IMAGE_TYPE]

    ret = requests.get(image_url)

    if ret.status_code != 200:
        raise Exception("Unable to download %s (code: %d)" %
                        (image_url, ret.status_code))

    img = Image.open(BytesIO(ret.content))
    img_array = np.array(img, dtype=np.float32)
    img_array = img_array / np.float32(256)

    input_sample[:, :] = img_array

    output_sample[:] = sample['annotations'][DIGIT_TYPE]
