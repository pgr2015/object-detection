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
import os
from typing import List, Callable, Union, Optional

import traceback

from multiprocessing import Process, Queue, Event


from com_bonseyes_base.formats.data.dataset.api import DataSetViewer, Datum


ProcessDatumFunction = Callable[[Optional[int], Datum, Queue], None]
WriteResultsFunction = Callable[[Queue], None]


def read_samples(samples_queue: Queue, dataset_viewers: List[DataSetViewer],
                 export_data_types: List[str], crash_event: Event):

    logging.info("Started read_samples process with pid %d" % os.getpid())

    try:

        for idx, viewer in enumerate(dataset_viewers):

            logging.info("Processing dataset_processing " + viewer.url)

            for datum in viewer.stream_data(export_data_types):

                if len(dataset_viewers) == 1:
                    samples_queue.put([None, datum])
                else:
                    samples_queue.put([idx, datum])

            logging.info("Finished processing dataset_processing " + viewer.url)

    except:

        tb = traceback.format_exc()
        logging.error("Error while processing sample:\n" + tb)

        crash_event.set()

        raise

    finally:
        logging.info("Finished read_samples process with pid %d" % os.getpid())


def process_samples(samples_queue: Queue, output_queue: Queue, process_datum_fun: ProcessDatumFunction, 
                    crash_event: Event):

    logging.info("Started process_samples process with pid %d" % os.getpid())

    try:

        while True:

            next_item = samples_queue.get()

            if next_item is None:
                break

            dataset_id, datum = next_item

            process_datum_fun(dataset_id, datum, output_queue)

    except:
        tb = traceback.format_exc()
        logging.error("Error while processing sample:\n" + tb)

        crash_event.set()

        raise

    finally:
        logging.info("Shutting down process_samples process pid = %d" % os.getpid())


def write_samples(write_out_function: WriteResultsFunction, output_queue: Queue, crash_event: Event):

    logging.info("Started write_samples process with pid %d" % os.getpid())

    try:
        write_out_function(output_queue)
    except:
        tb = traceback.format_exc()
        logging.error("Error while writing output:\n" + tb)

        crash_event.set()

        raise
    finally:
        logging.info("Shutting down write_samples process pid = %d" % os.getpid())


def read_datasets_and_process_samples(dataset_viewers: Union[DataSetViewer, List[DataSetViewer]],
                                      export_data_types: Union[str, List[str]],
                                      workers_count: int,
                                      process_datum_fun: ProcessDatumFunction,
                                      write_results_fun: WriteResultsFunction):

    logging.info("Starting processing dataset")

    if not isinstance(dataset_viewers, list):
        dataset_viewers = [dataset_viewers]

    if not isinstance(export_data_types, list):
        export_data_types = [export_data_types]

    crash_event = Event()

    samples_queue = Queue(10000)
    reader_worker = Process(target=lambda: read_samples(samples_queue, dataset_viewers,
                                                        export_data_types, crash_event))

    output_queue = Queue(10000)
    processors = []

    for i in range(workers_count):
        worker = Process(target=lambda: process_samples(samples_queue, output_queue,
                                                        process_datum_fun, crash_event))

        worker.start()
        processors.append(worker)

    writer_worker = Process(target=lambda: write_samples(write_results_fun, output_queue, crash_event))

    reader_worker.start()
    writer_worker.start()

    try:

        while reader_worker.is_alive():

            # check if processors or writer died
            if crash_event.is_set():
                raise Exception("Crashed")

            reader_worker.join(10)

        # reader finished, put kill pills in the workers queue
        for i in range(workers_count):
            samples_queue.put(None)

        for processor in processors:

            while processor.is_alive():

                # check if writer died
                if crash_event.is_set():
                    raise Exception("Crashed")

                processor.join(10)

        # processors finished, put kill pill for writer
        output_queue.put(None)

        writer_worker.join()

        if crash_event.is_set():
            raise Exception("Error while processing")

        logging.info("Finished to process dataset")

    except:

        logging.info("Crash detected, shutting down")

        reader_worker.terminate()

        for processor in processors:
            processor.terminate()

        writer_worker.terminate()

        raise


