#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import os
import tempfile
import zipfile
from shutil import copyfileobj, copy2

from com_bonseyes_base.formats.data.blob.api import BlobDataViewer
from com_bonseyes_base.formats.data.model.api import ModelEditor, BONSEYES_CAFFE_MODEL_TYPE, \
    BONSEYES_CAFFE_MODEL_SOLVER_CONFIG_BLOB, BONSEYES_CAFFE_MODEL_WEIGHTS_BLOB, \
    BONSEYES_CAFFE_MODEL_SOLVER_STATE_BLOB, BONSEYES_CAFFE_MODEL_TRAIN_NETWORK_BLOB, \
    BONSEYES_CAFFE_MODEL_DEPLOY_NETWORK_BLOB
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_base.lib.impl.utils import execute_with_logs
from bonseyes_objectdetection.mobilenetSSD import proto_generator, solver_generator

import google.protobuf.text_format as text_format
from caffe.proto import caffe_pb2 as cpb2


def perform_training_caffe(context: Context[ModelEditor], training_set: BlobDataViewer, label_map: str,
                           epochs: str, batch_size: str, background_class: str):

    with tempfile.TemporaryDirectory() as tmp_dir:

        # Get training dataset
        with training_set.view_content() as lmdb_zip:
            with zipfile.ZipFile(lmdb_zip, 'r') as z:
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
        copy2(os.path.join('/models/', 'MobileNetSSD_deploy.caffemodel'), weights_path)

        # Training
        execute_with_logs('/opt/caffe/build/tools/caffe', 'train', '--solver=' + solver_path,
                          '--weights=' + weights_path, '--gpu', '0')

        deploy_path = os.path.join(tmp_dir, 'deploy.prototxt')
        proto_generator(deploy_path, 'deploy', tmp_dir, label_map, int(num_labels),
                        int(batch_size), int(background_class))

        # save the model
        context.data.set_model_type(BONSEYES_CAFFE_MODEL_TYPE)

        with context.data.open_blob(BONSEYES_CAFFE_MODEL_TRAIN_NETWORK_BLOB, 'wb') as fpo:
            with open(train_path, 'rb') as fpi:
                copyfileobj(fpi, fpo)

        with context.data.open_blob(BONSEYES_CAFFE_MODEL_DEPLOY_NETWORK_BLOB, 'wb') as fpo:
            with open(deploy_path, 'rb') as fpi:
                copyfileobj(fpi, fpo)

        with context.data.open_blob(BONSEYES_CAFFE_MODEL_SOLVER_CONFIG_BLOB, 'wb') as fpo:
            with open(solver_path, 'rb') as fpi:
                copyfileobj(fpi, fpo)

        with context.data.open_blob(BONSEYES_CAFFE_MODEL_WEIGHTS_BLOB, 'wb') as fpo:
            weights_path = os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.caffemodel')
            with open(weights_path, 'rb') as fpi:
                copyfileobj(fpi, fpo)

        with context.data.open_blob(BONSEYES_CAFFE_MODEL_SOLVER_STATE_BLOB, 'wb') as fpo:
            state_path = os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.solverstate')
            with open(state_path, 'rb') as fpi:
                copyfileobj(fpi, fpo)


def create(context: Context[ModelEditor], training_set: BlobDataViewer, label_map: str,
           epochs: str = '120000', batch_size: str = '24', background_class: str = '0'):

    perform_training_caffe(context, training_set, label_map, epochs, batch_size, background_class)
