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
from jinja2 import Environment

from bonseyes.tool.storage import Encoding
from bonseyes.tool_api import DataSet


def create(version, datasets, condition):

    # compile the condition expression
    env = Environment()
    expr = env.compile_expression(condition)

    # merge the input datasets
    merged_samples = {}
    for dataset in datasets:
        dataset_samples = DataSet(dataset).samples

        for sample_name, sample_data in dataset_samples.items():

            if sample_name in merged_samples:
                merged_sample = merged_samples[sample_name]
            else:
                merged_sample = {}
                merged_samples[sample_name] = merged_sample

            for aspect in ['annotations', 'views', 'data']:
                if aspect in sample_data:
                    if aspect not in merged_sample:
                        merged_sample[aspect] = {}

                    merged_sample[aspect].update(sample_data[aspect])

    # filter the samples that match the condition
    filtered_samples = {}
    for sample_name, sample in merged_samples.items():
        if expr(sample_name=sample_name, sample=sample):
            filtered_samples[sample_name] = sample

    # write the output
    output_dir = version.create_data_directory()
    output_dir.create_file('dataset_processing.json', filtered_samples, encoding=Encoding.JSON)


