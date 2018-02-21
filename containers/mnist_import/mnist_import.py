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
import gzip
import os
import tempfile

import requests
from PIL import Image
import numpy as np
from io import BytesIO

from bonseyes_mnist import DIGIT_TYPE
from bonseyes_training_base import BONSEYES_PNG_IMAGE_TYPE


def download(url, output_file):

    if os.path.exists(output_file):
        raise Exception('Output file already exists')

    ret = requests.get(url, stream=True)

    if ret.status_code != 200:
        raise Exception('Unable to file (error code %d)' % ret.status_code)

    with open(output_file, 'wb') as fp:
        for chunk in ret.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fp.write(chunk)


def get_data(images_url, labels_url):

    with tempfile.TemporaryDirectory() as tmp_dir:

        images_file = os.path.join(tmp_dir, 'images.gz')

        download(images_url, images_file)

        with gzip.open(images_file, 'rb') as f:
            data = np.frombuffer(f.read(), np.uint8, offset=16)

        data = data.reshape(-1, 1, 28, 28)

        labels_file = os.path.join(tmp_dir, 'labels.gz')

        download(labels_url, labels_file)

        with gzip.open(labels_file, 'rb') as f:
            labels = np.frombuffer(f.read(), np.uint8, offset=8)

        for idx in range(0, data.shape[0]):

            image_array = np.empty((28, 28), np.uint8)
            image_array[:, :] = data[idx, :, :]

            im = Image.fromarray(image_array)

            out_file = BytesIO()

            im.save(out_file, format="png")

            out_file.seek(0)

            yield str(idx), {BONSEYES_PNG_IMAGE_TYPE: out_file}, {DIGIT_TYPE: int(labels[idx])}