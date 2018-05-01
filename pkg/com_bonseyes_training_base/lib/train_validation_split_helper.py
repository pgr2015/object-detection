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
import logging as log
from typing import Callable, List, Tuple

from com_bonseyes_base.formats.data.data_tensors.api import DataTensorsViewer, DimensionNames
from com_bonseyes_base.formats.data.training_tensors.api import TrainingTensorsEditor

TRAINING_GROUP_NAME = 'learning'
VALIDATION_GROUP_NAME = 'validation'

SplitIndexFunction = Callable[[DataTensorsViewer], Tuple[List[int], List[int]]]


def write_splitted_data(output: TrainingTensorsEditor,
                        data_tensors: DataTensorsViewer,
                        split_indexes_fun: SplitIndexFunction):

    log.info("Starting processing")

    with data_tensors:

        learning_indexes, validation_indexes = split_indexes_fun(data_tensors)

        if len(learning_indexes) == 0:
            raise Exception("Not enough learning samples")

        if len(validation_indexes) == 0:
            raise Exception("Not enough validation samples")

        classes = data_tensors.class_names

        log.info("Computing dimensions")

        input_dimensions = [(x.name, x.size) for x in data_tensors.input_data.dimensions.all
                            if x.name != DimensionNames.SAMPLE]

        output_dimensions = [(x.name, x.size) for x in data_tensors.output_data.dimensions.all
                             if x.name != DimensionNames.SAMPLE]

        log.info("Downloading sample names")
        samples = data_tensors.sample_names

        log.info("Downloading input data")
        input_samples = data_tensors.input_data[:]

        log.info("Downloading output data")
        output_samples = data_tensors.output_data[:]

        log.info("Writing learning data")

        with output:

            with output.learning_data as editor:

                editor.initialize(class_count=len(classes),
                                  input_dimensions=input_dimensions,
                                  output_dimensions=output_dimensions,
                                  input_data_type=data_tensors.input_data.data_type,
                                  output_data_type=data_tensors.output_data.data_type)

                editor.append_sample_data(names=[samples[x] for x in learning_indexes],
                                          input_data=input_samples[learning_indexes],
                                          output_data=output_samples[learning_indexes])

            log.info("Writing validation data")

            with output.validation_data as editor:
                editor.initialize(class_count=len(classes),
                                  input_dimensions=input_dimensions,
                                  output_dimensions=output_dimensions,
                                  input_data_type=data_tensors.input_data.data_type,
                                  output_data_type=data_tensors.output_data.data_type)

                editor.append_sample_data(names=[samples[x] for x in validation_indexes],
                                          input_data=input_samples[validation_indexes],
                                          output_data=output_samples[validation_indexes])

    log.info("Processing finished")
