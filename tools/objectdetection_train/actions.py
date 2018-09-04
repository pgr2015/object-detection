#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import os,time
import tempfile
import zipfile
import numpy as np
from shutil import copyfileobj, copy2

from com_bonseyes_base.formats.data.blob.api import BlobDataViewer
from com_bonseyes_base.formats.data.model.api import ModelEditor, BONSEYES_CAFFE_MODEL_TYPE, \
    BONSEYES_CAFFE_MODEL_SOLVER_CONFIG_BLOB, BONSEYES_CAFFE_MODEL_WEIGHTS_BLOB, \
    BONSEYES_CAFFE_MODEL_SOLVER_STATE_BLOB, BONSEYES_CAFFE_MODEL_TRAIN_NETWORK_BLOB, \
    BONSEYES_CAFFE_MODEL_DEPLOY_NETWORK_BLOB, BONSEYES_CAFFE_MODEL_MBN_BLOB
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_base.lib.impl.utils import execute_with_logs
from bonseyes_objectdetection.mobilenetSSD import proto_generator, solver_generator

import google.protobuf.text_format as text_format
from caffe.proto import caffe_pb2 as cpb2
import caffe

def merge_bn(net, nob):
    #print (type(net.params))
    for key in net.params.keys():
        if type(net.params[key]) is caffe._caffe.BlobVec:
            if key.endswith("/bn") or key.endswith("/scale"):
                continue
            else:
                conv = net.params[key]
                if not (key+"/bn") in net.params: #net.params.has_key(key + "/bn"):
                    for i, w in enumerate(conv):
                        nob.params[key][i].data[...] = w.data
                else:
                    bn = net.params[key + "/bn"]
                    scale = net.params[key + "/scale"]
                    wt = conv[0].data
                    channels = wt.shape[0]
                    bias = np.zeros(wt.shape[0])
                    if len(conv) > 1:
                        bias = conv[1].data
                    mean = bn[0].data
                    var = bn[1].data
                    scalef = bn[2].data
                    scales = scale[0].data
                    shift = scale[1].data
                    if scalef != 0:
                        scalef = 1. / scalef
                    mean = mean * scalef
                    var = var * scalef
                    rstd = 1. / np.sqrt(var + 1e-5)
                    rstd1 = rstd.reshape((channels,1,1,1))
                    scales1 = scales.reshape((channels,1,1,1))
                    wt = wt * rstd1 * scales1
                    bias = (bias - mean) * rstd * scales + shift
                    nob.params[key][0].data[...] = wt
                    nob.params[key][1].data[...] = bias

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

        train_model_path = os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.caffemodel')
        net = caffe.Net(train_path, train_model_path, caffe.TRAIN) #weights_path, caffe.TRAIN)  
        net_deploy = caffe.Net(deploy_path, caffe.TEST)
        merge_bn(net, net_deploy)
        net_deploy.save(os.path.join(tmp_dir,'tmp.caffemodel'))
        #time.sleep(300)

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

        with context.data.open_blob(BONSEYES_CAFFE_MODEL_MBN_BLOB, 'wb') as fpo:
            weights_path1 = os.path.join(tmp_dir, 'tmp.caffemodel')
            with open(weights_path1, 'rb') as fpi:
                copyfileobj(fpi, fpo)
        
        with context.data.open_blob(BONSEYES_CAFFE_MODEL_SOLVER_STATE_BLOB, 'wb') as fpo:
            state_path = os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.solverstate')
            with open(state_path, 'rb') as fpi:
                copyfileobj(fpi, fpo)


def create(context: Context[ModelEditor], training_set: BlobDataViewer, label_map: str,
           epochs: str = '120000', batch_size: str = '24', background_class: str = '0'):

    perform_training_caffe(context, training_set, label_map, epochs, batch_size, background_class)


