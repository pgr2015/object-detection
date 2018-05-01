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

import os

from zipfile import ZipFile

from bonseyes.training.base import BONSEYES_JPEG_IMAGE_TYPE, BONSEYES_PNG_IMAGE_TYPE, BONSEYES_TIFF_IMAGE_TYPE
from bonseyes.training.base.import_helper import write_dataset


def get_data(input_zip):

    types = {'jpg': BONSEYES_JPEG_IMAGE_TYPE,
             'jpeg': BONSEYES_JPEG_IMAGE_TYPE,
             'png': BONSEYES_PNG_IMAGE_TYPE,
             'tiff': BONSEYES_TIFF_IMAGE_TYPE}

    with ZipFile(input_zip) as z:

        for file_name in z.namelist():

            file_name = os.path.normpath(file_name)

            image_type = None
            for ext in types:
                if file_name.lower().endswith(ext):
                    image_type = types[ext]

            if image_type is None:
                continue

            sample_id = file_name.rsplit('.', 1)[0].replace('/', '_').replace(' ', '_')

            sample_annotation = {}

            sample_data = {image_type: z.open(file_name)}

            yield sample_id, sample_data, sample_annotation


def create(version, archive):
    data = get_data(archive)
    write_dataset(version, data)
