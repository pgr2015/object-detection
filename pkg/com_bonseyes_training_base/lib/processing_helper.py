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
import shutil
import logging
from typing import Callable, List, Iterable, Tuple

from multiprocessing import Queue

from bonseyes.training.base.dataset_parallelize_process import read_datasets_and_process_samples
from bonseyes.training.base import BONSEYES_JPEG_IMAGE_TYPE, \
                                   BONSEYES_PNG_IMAGE_TYPE, \
                                   BONSEYES_TIFF_IMAGE_TYPE
from bonseyes_formats.data.dataset import DataSetEditor, DataSetViewer, Sample, Datum


def sample_processor(output_dir, process_sample_fun, dataset_id, sample_name, sample, data,
                     results_queue):

    sample_dir = output_dir.create_dir(sample_name)

    data_view_map = {}

    for data_view_type, data_view_fp in process_sample_fun(sample_name, data):
        with sample_dir.open_file(data_view_type, mode='wb') as fp:
            shutil.copyfileobj(data_view_fp, fp)

        data_view_fp.close()

        data_view_map[data_view_type] = os.path.join(sample_name, data_view_type)

    if len(data_view_map) != 0:
        sample_data = {'views': data_view_map}
        if 'annotations' in sample:
            sample_data['annotations'] = sample['annotations']

        results_queue.put((sample_name, sample_data))


def dataset_writer(version, results_queue, total_samples):

    logging.info("Starting writer pid = %d " % os.getpid())

    samples = {}

    metric = DatasetMetric(version)

    # collect all results in a json
    while True:

        next_result = results_queue.get()

        if next_result is None:
            break

        sample_name, sample_data = next_result
        samples[sample_name] = sample_data

        metric.update(samples)

    metric.flush()

    version.data.create_file('dataset_processing.json', samples, encoding=Encoding.JSON)

    logging.info("Shutting down writer pid = %d" % os.getpid())


ProcessingFunction = Callable[[Sample], Iterable[Tuple[str, bytes]]]

def process_data(editor: DataSetEditor,
                 input_dataset: List[DataSetViewer],
                 processing_fun: ProcessingFunction,
                 workers_count: int=1):

    ProcessDatumFunction = Callable[[Optional[int], Datum, Queue], None]
    WriteResultsFunction = Callable[[Queue], None]

    logging.info("Starting processing")

    output_dir = version.create_data_directory()

    def bound_processing_fun(dataset_id: int, datum: Datum, queue: Queue):
        sample_processor(output_dir, processing_fun, *args)

    def bound_write_fun(*args):
        dataset_writer(version, *args)

    data_names = [BONSEYES_JPEG_IMAGE_TYPE, BONSEYES_PNG_IMAGE_TYPE, BONSEYES_TIFF_IMAGE_TYPE]

    read_datasets_and_process_samples(dataset_viewers=input_dataset,
                                      export_data_types=data_names,
                                      workers_count=workers_count,
                                      process_datum_fun=bound_processing_fun,
                                      write_results_fun=bound_write_fun)

    logging.info("Processing finished")
