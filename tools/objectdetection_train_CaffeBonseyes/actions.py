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

def download(url, output_file):
	log.info (url)
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


def perform_training_caffe(context: Context[BlobDataEditor], model: BlobDataEditor, training_set: DataTensorsViewer, epochs: str, batch: str):

	#with context.data.edit_content() as output_path:
	with tempfile.TemporaryDirectory() as tmp_dir:
		#os.mkdir (output_path)
		with zipfile.ZipFile(training_set, 'r') as z:
			z.extractall(tmp_dir)

		with  model.view_content() as model_zip:
			with zipfile.ZipFile(model_zip, 'r') as z:
				z.extractall(tmp_dir)

		download('http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/training/labelmap_youtubebb.prototxt', os.path.join ("/volumes/data", "labelmap_youtubebb.prototxt"))
		download("http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/training/gen_CaffeBonseyes.py", os.path.join("/volumes/data", "gen_CaffeBonseyes.py"))
		download("http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/training/solverGenerator_CaffeBonseyes.py", os.path.join("/volumes/data", "solverGenerator_CaffeBonseyes.py"))

		shutil.copy2(os.path.join("/volumes/data", "labelmap_youtubebb.prototxt"),os.path.join(tmp_dir, "labelmap_youtubebb.prototxt"));
		shutil.copy2(os.path.join("/volumes/data", "gen_CaffeBonseyes.py"),os.path.join(tmp_dir, "gen_CaffeBonseyes.py"));
		shutil.copy2(os.path.join("/volumes/data", "solverGenerator_CaffeBonseyes.py"),os.path.join(tmp_dir, "solverGenerator_CaffeBonseyes.py"));
		
		labelmap_path = os.path.join(tmp_dir, "labelmap_youtubebb.prototxt")
		lmdb_path = os.path.join(tmp_dir, "youtube-bb_trainval_lmdb")

		#================Train.prototxt================
		cmd = ['python', os.path.join(tmp_dir, "gen_CaffeBonseyes.py"), "-s", "train", "-d", lmdb_path, "-l", labelmap_path, "-c", "24", "-b", batch]

		process = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		process.wait()
		train_path = os.path.join(tmp_dir, "MobileNetSSD_train.prototxt")
		proto = open(train_path, 'wb')
		output, errors = process.communicate()
		log.info(errors)

		proto.write(output)

		proto.flush()
		proto.close()
		#================Train.prototxt================

        #================Solver.prototxt================
		cmd = ['python', os.path.join(tmp_dir, "solverGenerator_CaffeBonseyes.py"), "-n", train_path, "-it", epochs, "-o", tmp_dir + "/"]
		process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		process.wait()

		solver_path = os.path.join(tmp_dir, "solver2.prototxt")
		proto = open(solver_path, 'wb')
		stdout, stderr = process.communicate()
		proto.write(stdout)

		proto.flush()
		proto.close()

        #================Solver.prototxt================

		log.info("Start train")

		weights_path = os.path.join(tmp_dir, "trained-model.caffemodel")
		full_command = ['/opt/caffe/build/tools/caffe', 'train', '--solver=' + solver_path, '--weights='+ weights_path, '--gpu', '0']

		process = subprocess.Popen(full_command, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)#, shell=True)

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
				z.write(os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.caffemodel'), arcname='trained-model.caffemodel')
				z.write(os.path.join(tmp_dir, 'snapshot_iter_' + epochs + '.solverstate'), arcname='trained-model.solverstate')



def create(context: Context[BlobDataEditor], model: BlobDataEditor, training_set: DataTensorsViewer, epochs: str="28000", batch="24"):#BlobDataEditor

	print ('hola ')
	print (epochs)
	log.info (training_set)
	lmdb_path =  '/'+training_set.split('/')[1]+'/'+training_set.split('/')[2]+'/data'
	log.info(lmdb_path)

	perform_training_caffe (context, model, training_set, epochs, batch)
