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

def download(url, output_file):
    log.info (url)
    log.info (output_file)
	
    if os.path.exists(output_file):
        log.info ('Output file already exists')
    else:
        ret = requests.get(url, stream=True)
        if ret.status_code != 200:
            raise Exception('Unable to file (error code %d)' % ret.status_code)

        with open(output_file, 'wb') as fp:
            for chunk in ret.iter_content(chunk_size=1024 * 1024):
                if chunk:   
                    fp.write(chunk)


def perform_bebenchmarking (context: Context[BlobDataEditor], model: BlobDataEditor, training_set: DataTensorsViewer, epochs: str):

    with tempfile.TemporaryDirectory() as tmp_dir:

        with  model.view_content() as model_zip:
            with zipfile.ZipFile(model_zip, 'r') as z:
                z.extractall(tmp_dir)
        
        log.info (training_set)
        with zipfile.ZipFile (training_set, 'r') as z:
            z.extractall(tmp_dir)

        download("http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/training/labelmap_youtubebb.prototxt", os.path.join("/volumes/data", "labelmap_youtubebb.prototxt"))
        download("http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/testing/solverGeneratorTesting.py", os.path.join("/volumes/data", "solverGeneratorTesting.py"))

        shutil.copy2(os.path.join("/volumes/data", "labelmap_youtubebb.prototxt"),os.path.join(tmp_dir, "labelmap_youtubebb.prototxt"));
        shutil.copy2(os.path.join("/volumes/data", "solverGeneratorTesting.py"),os.path.join(tmp_dir, "solverGeneratorTesting.py"));

        shutil.move (os.path.join(tmp_dir, 'youtube-bb_trainval_lmdb'), os.path.join(tmp_dir, 'youtube-bb_test_lmdb'))

        with zipfile.ZipFile (training_set) as z:
            z.extractall(tmp_dir)
        
        lmdb_path_tra = os.path.join(tmp_dir, 'youtube-bb_trainval_lmdb')
        lmdb_path_test = os.path.join(tmp_dir, 'youtube-bb_test_lmdb')

        labelmap_path = os.path.join(tmp_dir, 'labelmap_youtubebb.prototxt')

        download("http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/training/gen.py", os.path.join("/volumes/data", "gen.py"))
        shutil.copy2(os.path.join("/volumes/data", "gen.py"),os.path.join(tmp_dir, "gen.py"));

        # ================Train.prototxt================
        cmd = ['python', os.path.join(tmp_dir, "gen.py"), "-s", "train", "-d", lmdb_path_tra, "-l", labelmap_path, "-c", "24", "-b", "24"]

        process = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        train_path = os.path.join(tmp_dir, "MobileNetSSD_train2.prototxt")
        proto = open(train_path, 'wb')
        output, errors = process.communicate()
        log.info(errors)

        proto.write(output)

        proto.flush()
        proto.close()
        
        #================Test.prototxt================
        cmd = ['python', os.path.join(tmp_dir, "gen.py"), "-s", "test", "-d", lmdb_path_test, "-l", labelmap_path, "-c", "24", "-b", "24"]

        process = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        test_path = os.path.join(tmp_dir, "MobileNetSSD_test.prototxt")
        proto = open(test_path, 'wb')
        output, errors = process.communicate()
        log.info(errors)

        proto.write(output)

        proto.flush()
        proto.close()

        #================Solver.prototxt================
        num_iter_tra = "0"
        cmd = ['python', os.path.join(tmp_dir, "solverGeneratorTesting.py"), "-ntr", train_path, "-nte", test_path,  "-it", num_iter_tra, "-itt", epochs, "-o", tmp_dir + "/"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        process.wait()

        solver_path = os.path.join(tmp_dir, "solver_test.prototxt")
        proto = open(solver_path, 'wb')
        stdout, stderr = process.communicate()
        proto.write(stdout)

        proto.flush()
        proto.close()

        #================End Solver.prototxt================

        log.info("Start benchmark")
        weights_path = os.path.join (tmp_dir, "trained-model.caffemodel")
        full_command = ['/opt/caffe/build/tools/caffe', 'train', '--solver=' + solver_path, '--weights='+ weights_path, '--gpu', '0'];
        # /media/mila/DATOS/BONSEYES/object_detection/MobileNet-SSD/caffe-ssd/build/tools/caffe train -solver solver.prototxt -weights MobileNetSSD_deploy.caffemodel -gpu 0
        # '--weights='+tmp_dir+'MobileNetSSD_deploy.caffemodel',
        process = subprocess.Popen(full_command, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)#, shell=True)

        for line in process.stdout:
            log.info(line.decode('utf-8', 'ignore').strip())

        process.wait()
        output, errors = process.communicate()
        log.info(".....................................")
        log.info(errors)
        
        AP  = [''] * 25 
        
        with context.data.edit_content() as output_path:
            name = output_path.split('/')[2]
            log.info  (name)
            logfile_path = os.path.join ('/data', name)

            logfile_path = os.path.join(logfile_path, 'history/0/log')
            file = open(logfile_path, 'r') 
            for line in file: 
                if 'class' in line:
                    if not '_class_' in line:
                        class_number=line.split('class')[1]
                        class_number=class_number.split(':')[0]
                    
                        AP_class=line.split(': ')[1]    
                        AP_class=AP_class.split('\n')[0]
                        AP[int(class_number)] = AP_class 

                if 'detection_eval =' in line: 
                    AP_class=line.split('= ')[1]
                    AP_class=AP_class.split('\n')[0]
                    AP[24] = AP_class 
        
            file.close()
            os.mkdir(output_path)
            with open(os.path.join(output_path,'data.json'), 'w') as fp:
                json.dump(OrderedDict(
                    [('AP class 0 ', AP[0]),
                    ('AP class 1 ',AP[1]),
                    ('AP class 2 ',AP[2]),
                    ('AP class 3 ',AP[3]), 
                    ('AP class 4 ',AP[4]),
                    ('AP class 5 ',AP[5]),
                    ('AP class 6 ',AP[6]),
                    ('AP class 7 ',AP[7]),
                    ('AP class 8 ',AP[8]),
                    ('AP class 9 ',AP[9]),
                    ('AP class 10 ',AP[10]),
                    ('AP class 11 ',AP[11]),
                    ('AP class 12 ',AP[12]),
                    ('AP class 13 ',AP[13]),
                    ('AP class 14 ',AP[14]),
                    ('AP class 15 ',AP[15]),
                    ('AP class 16 ',AP[16]),
                    ('AP class 17 ',AP[17]),
                    ('AP class 18 ',AP[18]),
                    ('AP class 19 ',AP[19]),
                    ('AP class 20 ',AP[20]),
                    ('AP class 21 ',AP[21]),
                    ('AP class 23 ',AP[23]),
                    ('mAP ',AP[24])]
                ),fp)    

def create(context: Context[BlobDataEditor], model: BlobDataEditor, training_set: DataTensorsViewer, epochs: str="5000"):#tensor: DataTensorsViewer, model: BlobDataViewer, pairs: str):

    log.info (context)
    

    perform_bebenchmarking(context, model, training_set, epochs)