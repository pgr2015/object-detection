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
import json
from io import TextIOWrapper

from zipfile import ZipFile

from bonseyes.training.base.import_helper import write_dataset


def get_data(input_zip):

    with ZipFile(input_zip) as z:

        with z.open('dataset_processing.json') as fp:
            metadata = json.load(TextIOWrapper(fp))

        for sample_name, sample in metadata.items():

            views = {view: z.open(path) for view, path in sample.get('views', {}).items()}
            data = {data: z.open(path) for data, path in sample.get('data', {}).items()}
            annotations = sample.get('annotations', {})

            yield sample_name, data, views, annotations


def create(version, archive):
    data = get_data(archive)
    write_dataset(version, data)
