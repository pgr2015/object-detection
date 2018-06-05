import os
import json
from collections import OrderedDict
import zipfile
import tempfile
from shutil import copyfileobj

from com_bonseyes_base.formats.data.blob.api import BlobDataViewer
from com_bonseyes_base.formats.data.model.api import ModelEditor, \
    BONSEYES_CAFFE_MODEL_WEIGHTS_BLOB
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_base.lib.impl.utils import execute_with_logs
from bonseyes_objectdetection.mobilenetSSD import proto_generator, solver_generator_test
from com_bonseyes_base.formats.data.blob.api import BlobDataEditor

import google.protobuf.text_format as text_format
from caffe.proto import caffe_pb2 as cpb2


def perform_benchmarking(context: Context[BlobDataEditor], model: ModelEditor, test_set: BlobDataViewer,
                         label_map: str, epochs: str, batch_size: str, background_class: str):

    with tempfile.TemporaryDirectory() as tmp_dir:

        model_folder_path = os.path.join(tmp_dir, 'model')
        os.mkdir(model_folder_path)

        weights_path = os.path.join(model_folder_path, 'trained-model.caffemodel')

        with model.open_blob(BONSEYES_CAFFE_MODEL_WEIGHTS_BLOB, 'rb') as fpi:
            with open(weights_path, 'wb') as fpo:
                copyfileobj(fpi, fpo)

        lmdb_train_folder = os.path.join(tmp_dir, 'dataset_train')
        lmdb_test_folder = os.path.join(tmp_dir, 'dataset_test')
        # Get test dataset
        with test_set.view_content() as lmdb_zip:
            with zipfile.ZipFile(lmdb_zip, 'r') as z:
                z.extractall(lmdb_train_folder)
                z.extractall(lmdb_test_folder)

        # Generate MobileNetSSD_train.prototxt and MobileNetSSD_test.prototxt
        label_names = {}
        with open(label_map, 'r') as label_map_file:
            labels = cpb2.LabelMap()
            text_format.Merge(str(label_map_file.read()), labels)
            num_labels = len(labels.item)
            for i in range(0, num_labels):
                label_names[str(labels.item[i].label)] = labels.item[i].display_name
        train_path = os.path.join(tmp_dir, 'MobileNetSSD_train.prototxt')
        test_path = os.path.join(tmp_dir, 'MobileNetSSD_test.prototxt')
        proto_generator(train_path, 'train', lmdb_train_folder, label_map, int(num_labels),
                        int(batch_size), int(background_class))
        proto_generator(test_path, 'test', lmdb_test_folder, label_map, int(num_labels),
                        int(batch_size), int(background_class))

        # Generate Solver
        solver_path = os.path.join(tmp_dir, 'solver.prototxt')
        solver_generator_test(solver_path, train_path, test_path, int(epochs), tmp_dir + '/', 'detection')

        # Training
        execute_with_logs('/opt/caffe/build/tools/caffe', 'train', '--solver=' + solver_path,
                          '--weights=' + weights_path, '--gpu', '0')

        AP = OrderedDict()

        with context.data.edit_content() as output_path:
            name = output_path.split('/')[2]
            logfile_path = os.path.join('/data', name)

            logfile_path = os.path.join(logfile_path, 'history/0/log')
            with open(logfile_path, 'r') as logfile:
                for line in logfile:
                    if 'class' in line and not '_class_' in line:
                        from_class = line.split('class')[1]
                        class_number = from_class.split(':')[0]
                        AP_class = from_class.split(': ')[1]
                        AP_class = AP_class.split('\n')[0]
                        AP['AP class ' + class_number + '-' + label_names[class_number]] = AP_class
                    if 'detection_eval =' in line:
                        mAP = line.split('= ')[1]
                        mAP = mAP.split('\n')[0]
                        AP['mAP'] = mAP

            with open(output_path, 'w') as fp:
                json.dump(AP, fp)


def create(context: Context[BlobDataEditor], model: ModelEditor, test_set: BlobDataViewer, label_map: str,
           epochs: str = '5000', batch_size: str = '6', background_class: str = '0'):

    perform_benchmarking(context, model, test_set, label_map, epochs, batch_size, background_class)
