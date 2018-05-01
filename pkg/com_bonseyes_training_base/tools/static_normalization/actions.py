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
import logging

import h5py
import numpy

from bonseyes.training.base import NORMALIZATION_PARAMS_MEAN_DATASET_NAME, NORMALIZATION_PARAMS_STD_DATASET_NAME


def create(version, width, height, mean, std):

    logging.info("Starting processing")

    mean_tensor = numpy.ones(shape=(int(height), int(width))) * float(mean)
    std_tensor = numpy.ones(shape=(int(height), int(width))) * float(std)

    with version.edit_data_file() as output_file:
        with h5py.File(output_file, 'w') as f:
            f.create_dataset(NORMALIZATION_PARAMS_MEAN_DATASET_NAME, data=mean_tensor)
            f.create_dataset(NORMALIZATION_PARAMS_STD_DATASET_NAME, data=std_tensor)

    logging.info("Completed")

