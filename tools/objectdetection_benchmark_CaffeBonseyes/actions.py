import os
import subprocess
import logging as log
import requests
import json
from collections import OrderedDict
import zipfile
import tempfile
import shutil

from com_bonseyes_base.formats.data.blob.api import BlobDataEditor
from com_bonseyes_base.formats.data.data_tensors.api import DataTensorsViewer, DimensionNames
from com_bonseyes_base.lib.api.tool import Context
from bonseyes_youtubebb.mobilenetSSD import proto_generator_BonseyesCaffe, solver_generator_test_BonseyesCaffe


def perform_bebenchmarking(context: Context[BlobDataEditor], model: BlobDataEditor, training_set: DataTensorsViewer, epochs: str, batch_size: str):

    with tempfile.TemporaryDirectory() as tmp_dir:

        with  model.view_content() as model_zip:
            with zipfile.ZipFile(model_zip, 'r') as z:
                z.extractall(tmp_dir)

        log.info(training_set)
        with zipfile.ZipFile(training_set, 'r') as z:
            z.extractall(tmp_dir)

        shutil.copy2(os.path.join("/volumes/data", "labelmap_youtubebb.prototxt"),
                     os.path.join(tmp_dir, "labelmap_youtubebb.prototxt"));

        shutil.move(os.path.join(tmp_dir, 'youtube-bb_trainval_lmdb'), os.path.join(tmp_dir, 'youtube-bb_test_lmdb'))

        with zipfile.ZipFile(training_set) as z:
            z.extractall(tmp_dir)

        lmdb_path_tra = os.path.join(tmp_dir, 'youtube-bb_trainval_lmdb')
        lmdb_path_test = os.path.join(tmp_dir, 'youtube-bb_test_lmdb')

        labelmap_path = os.path.join(tmp_dir, 'labelmap_youtubebb.prototxt')

        # ================Train.prototxt================

        train_path = os.path.join(tmp_dir, "MobileNetSSD_train2.prototxt")
        proto_generator_BonseyesCaffe(train_path, "train", lmdb_path_tra, labelmap_path, 24, int(batch_size), False, 22)

        # ================Test.prototxt================

        test_path = os.path.join(tmp_dir, "MobileNetSSD_test.prototxt")
        proto_generator_BonseyesCaffe(test_path, "test", lmdb_path_test, labelmap_path, 24, int(batch_size), False, 22)

        # ================Solver.prototxt================

        solver_path = os.path.join(tmp_dir, "solver.prototxt")
        solver_generator_test_BonseyesCaffe(solver_path, train_path, test_path, int(epochs), tmp_dir + "/", "detection")

        # ================End Solver.prototxt================

        log.info("Start benchmark")
        weights_path = os.path.join(tmp_dir, "trained-model.caffemodel")
        full_command = ['/opt/caffe/build/tools/caffe', 'train', '--solver=' + solver_path, '--weights=' + weights_path,
                        '--gpu', '0'];
        # /media/mila/DATOS/BONSEYES/object_detection/MobileNet-SSD/caffe-ssd/build/tools/caffe train -solver solver.prototxt -weights MobileNetSSD_deploy.caffemodel -gpu 0
        # '--weights='+tmp_dir+'MobileNetSSD_deploy.caffemodel',
        process = subprocess.Popen(full_command, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)  # , shell=True)

        for line in process.stdout:
            log.info(line.decode('utf-8', 'ignore').strip())

        process.wait()
        output, errors = process.communicate()
        log.info(".....................................")
        log.info(errors)

        AP = [''] * 25

        with context.data.edit_content() as output_path:
            name = output_path.split('/')[2]
            log.info(name)
            logfile_path = os.path.join('/data', name)

            logfile_path = os.path.join(logfile_path, 'history/0/log')
            file = open(logfile_path, 'r')
            for line in file:
                if 'class' in line:
                    if not '_class_' in line:
                        class_number = line.split('class AP ')[1]
                        class_number = class_number.split(':')[0]

                        AP_class = line.split(': ')[1]
                        AP_class = AP_class.split('\n')[0]
                        AP[int(class_number)] = AP_class

                if 'detection_eval =' in line:
                    AP_class = line.split('= ')[1]
                    AP_class = AP_class.split('\n')[0]
                    AP[24] = AP_class

            file.close()
            os.mkdir(output_path)
            with open(os.path.join(output_path, 'data.json'), 'w') as fp:
                json.dump(OrderedDict(
                    [('AP class 0 ', AP[0]),
                     ('AP class 1 ', AP[1]),
                     ('AP class 2 ', AP[2]),
                     ('AP class 3 ', AP[3]),
                     ('AP class 4 ', AP[4]),
                     ('AP class 5 ', AP[5]),
                     ('AP class 6 ', AP[6]),
                     ('AP class 7 ', AP[7]),
                     ('AP class 8 ', AP[8]),
                     ('AP class 9 ', AP[9]),
                     ('AP class 10 ', AP[10]),
                     ('AP class 11 ', AP[11]),
                     ('AP class 12 ', AP[12]),
                     ('AP class 13 ', AP[13]),
                     ('AP class 14 ', AP[14]),
                     ('AP class 15 ', AP[15]),
                     ('AP class 16 ', AP[16]),
                     ('AP class 17 ', AP[17]),
                     ('AP class 18 ', AP[18]),
                     ('AP class 19 ', AP[19]),
                     ('AP class 20 ', AP[20]),
                     ('AP class 21 ', AP[21]),
                     ('AP class 23 ', AP[23]),
                     ('mAP ', AP[24])]
                ), fp)

def create(context: Context[BlobDataEditor], model: BlobDataEditor, training_set: DataTensorsViewer, epochs: str="5000", batch_size: str = "6"):#tensor: DataTensorsViewer, model: BlobDataViewer, pairs: str):

    log.info (context)
    
    perform_bebenchmarking(context, model, training_set, epochs, batch_size)
