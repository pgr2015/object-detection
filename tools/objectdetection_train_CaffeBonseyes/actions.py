#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import os
import tempfile
import zipfile

import requests
import subprocess
import logging as log
import shutil

from com_bonseyes_base.formats.data.blob.api import BlobDataEditor
from com_bonseyes_base.formats.data.data_tensors.api import DataTensorsViewer, DimensionNames
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_base.lib.impl.utils import execute_with_logs
from bonseyes_youtubebb.mobilenetSSD import proto_generator_BonseyesCaffe, solver_generator_BonseyesCaffe


def perform_training_caffe(context: Context[BlobDataEditor], model: BlobDataEditor, training_set: DataTensorsViewer, epochs: str, batch_size: str):

    with tempfile.TemporaryDirectory() as tmp_dir:
        with  model.view_content() as model_zip:
            with zipfile.ZipFile(model_zip, 'r') as z:
                z.extractall(tmp_dir)

        log.info(training_set)
        with zipfile.ZipFile(training_set, 'r') as z:
            z.extractall(tmp_dir)

        shutil.copy2(os.path.join("/volumes/data", "labelmap_youtubebb.prototxt"),
                     os.path.join(tmp_dir, "labelmap_youtubebb.prototxt"))
        labelmap_path = os.path.join(tmp_dir, "labelmap_youtubebb.prototxt")
        lmdb_path = os.path.join(tmp_dir, "youtube-bb_trainval_lmdb")

        # ================Train.prototxt================
        train_path = os.path.join(tmp_dir, "MobileNetSSD_train.prototxt")
        proto_generator_BonseyesCaffe(train_path, "train", lmdb_path, labelmap_path, 24, int(batch_size), False, 22)

        # ================Solver.prototxt================

        solver_path = os.path.join(tmp_dir, "solver.prototxt")
        solver_generator_BonseyesCaffe(solver_path, train_path, int(epochs), tmp_dir + "/", "detection")

        log.info("Start train")

        real_weights_config_path = os.path.join(tmp_dir, "trained-model.caffemodel")

        full_command = ['/opt/caffe/build/tools/caffe', 'train', '--solver=' + solver_path,
                        '--weights=' + real_weights_config_path, '--gpu', '0']
        # # /media/mila/DATOS/BONSEYES/object_detection/MobileNet-SSD/caffe-ssd/build/tools/caffe train -solver solver.prototxt -weights MobileNetSSD_deploy.caffemodel -gpu 0
        # # '--weights='+tmp_dir+'MobileNetSSD_deploy.caffemodel',
        process = subprocess.Popen(full_command, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   close_fds=True)  # , shell=True)
        for line in process.stdout:
            log.info(line.decode('utf-8', 'ignore').strip())

        process.wait()
        output, errors = process.communicate()
        log.info(".....................................")
        log.info(errors)
        with context.data.edit_content() as output_file:
            with zipfile.ZipFile(output_file, 'a') as z:
                z.write(train_path, arcname='MobileNetSSD_train.prototxt')
                z.write(solver_path, arcname='solver.prototxt')
                z.write(os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.caffemodel'),
                        arcname='trained-model.caffemodel')
                z.write(os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.solverstate'),
                        arcname='trained-model.solverstate')


def create(context: Context[BlobDataEditor], model: BlobDataEditor, training_set: DataTensorsViewer,
           epochs: str = "28000", batch_size: str = "12"):  # BlobDataEditor

    log.info(training_set)
    lmdb_path = '/' + training_set.split('/')[1] + '/' + training_set.split('/')[2] + '/data'
    log.info(lmdb_path)

    perform_training_caffe(context, model, training_set, epochs, batch_size)
