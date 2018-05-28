#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import os
import tempfile
import zipfile
import shutil

from com_bonseyes_base.formats.data.blob.api import BlobDataEditor
from com_bonseyes_base.formats.data.data_tensors.api import DataTensorsViewer
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_base.lib.impl.utils import execute_with_logs
from bonseyes_objectdetection.mobilenetSSD import proto_generator, solver_generator

import google.protobuf.text_format as text_format
from caffe.proto import caffe_pb2 as cpb2


def perform_training_caffe(context: Context[BlobDataEditor], training_set: DataTensorsViewer, label_map: str,
                           epochs: str, batch_size: str, background_class: str):

    with tempfile.TemporaryDirectory() as tmp_dir:

        with zipfile.ZipFile(training_set, 'r') as z:
            z.extractall(tmp_dir)

        # Generate MobileNetSSD_train.prototxt
        with open(label_map, 'r') as label_map_file:
            labels = cpb2.LabelMap()
            text_format.Merge(str(label_map_file.read()), labels)
            num_labels = len(labels.item)
        train_path = os.path.join(tmp_dir, 'MobileNetSSD_train.prototxt')
        proto_generator(train_path, 'train', tmp_dir, label_map, int(num_labels),
                        int(batch_size), int(background_class))

        # Generate Solver
        solver_path = os.path.join(tmp_dir, 'solver.prototxt')
        solver_generator(solver_path, train_path, int(epochs), tmp_dir + '/', 'detection')

        # Weights from VOC
        weights_path = os.path.join(tmp_dir, 'MobileNetSSD_deploy.caffemodel')
        shutil.copy2(os.path.join('/models/', 'MobileNetSSD_deploy.caffemodel'), weights_path)

        # Training
        execute_with_logs('/opt/caffe/build/tools/caffe', 'train', '--solver=' + solver_path,
                          '--weights=' + weights_path, '--gpu', '0')

        # Store results
        with context.data.edit_content() as output_file:
            with zipfile.ZipFile(output_file, 'a') as z:
                z.write(train_path, arcname='MobileNetSSD_train.prototxt')
                z.write(solver_path, arcname='solver.prototxt')
                z.write(os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.caffemodel'),
                        arcname='trained-model.caffemodel')
                z.write(os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.solverstate'),
                        arcname='trained-model.solverstate')


def create(context: Context[BlobDataEditor], training_set: DataTensorsViewer, label_map: str, epochs: str = '120000',
           batch_size: str = '24', background_class: str = '0'):

    perform_training_caffe(context, training_set, label_map, epochs, batch_size, background_class)
