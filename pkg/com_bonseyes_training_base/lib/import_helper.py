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
import logging
from typing import Dict, Optional, Tuple, Union, Iterator

import shutil

import os

from com_bonseyes_base.formats.data.dataset.api import DataSetEditor
from com_bonseyes_base.formats.metrics.dataset_processing.api import DatasetProcessingMetricEditor


def write_dataset(editor: DataSetEditor, data_in: Union[Iterator[Tuple[str, Dict, Dict]],
                                                        Iterator[Tuple[str, Dict, Dict, Dict]]],
                  metric: Optional[DatasetProcessingMetricEditor]=None):

    with editor.edit_content() as output_path:

        samples = {}

        # write out the data and annotations
        logging.info('Importing data and annotations')

        for data_item in data_in:

            if len(data_item) == 3:
                sample_name, data, annotations = data_item
                views = {}
            elif len(data_item) == 4:
                sample_name, data, views, annotations = data_item
            else:
                raise Exception("Cannot write data for item " + str(data_item))

            samples[sample_name] = {}

            def write_aspect(aspect_name, aspect_data):

                data_map = {}

                for data_type, data_fp in aspect_data.items():

                    data_map[data_type] = sample_name + '_' + aspect_name + '_' + data_type

                    with open(os.path.join(output_path, data_map[data_type]), 'wb') as fp:
                        shutil.copyfileobj(data_fp, fp)

                    data_fp.close()

                samples[sample_name][aspect_name] = data_map

            if len(data) > 0:
                write_aspect('data', data)

            if len(views) > 0:
                write_aspect('views', views)

            if len(annotations) > 0:
                samples[sample_name]['annotations'] = annotations

            if metric is not None:
                metric.set_processed_samples(len(samples))

        with open(os.path.join(output_path, 'dataset.json'), 'w') as fp:
            json.dump(samples, fp)

    logging.info('Import process finished')
