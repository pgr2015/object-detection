#
# UCLM CONFIDENTIAL
#
# Copyright (c) 2017 UCLM SA. All Rights Reserved.
#
import gzip
import os
import tempfile
import tarfile
import csv
import time

import requests
from PIL import Image
import numpy as np
from io import BytesIO

import logging as log

from bonseyes_youtubebb import DIGIT_TYPE

from com_bonseyes_base.formats.data.dataset.api import DataSetEditor
from com_bonseyes_base.lib.api.tool import Context
from com_bonseyes_training_base.lib import BONSEYES_PNG_IMAGE_TYPE
from com_bonseyes_training_base.lib.import_helper import write_dataset
#from bonseyes_youtubebb import YOUTUBEBB_ID_LABEL

def download(url, output_file):

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


def get_data(images: str, labels:str, context: Context[DataSetEditor]):
	log.info ("hola")

	images_path = os.path.join ("/volumes/data", images.split('/')[-1])
	labels_path = os.path.join ("/volumes/data", labels.split('/')[-1])
	download(images, images_path)
	download(labels, labels_path)

	samples_names = []
	dataset_name = images.split('/')[-1]
	dataset_name = dataset_name.split('.')[0]
	log.info (dataset_name)
	with tempfile.TemporaryDirectory() as tmp_dir:
		with context.data.edit_content() as output_file:
			with tarfile.open(images_path, 'r') as tar:
				for member in tar.getmembers():

					file = member.name
					file = os.path.normpath(file)

					if (not file.endswith('.png')):
						continue

					sample_id = os.path.basename(file)[:-4]

					samples_names.append(sample_id)
					tar.extract(member, tmp_dir)

			with open(labels_path, 'r') as csvfile:

				reader = csv.reader(csvfile)
				previous_video = str('')
				second = 0

				for row in reader:
					video_id = row[0]+'+'+row[2]+'+'+row[4]
					
					if  video_id != previous_video:
						second=0
						previous_video = str('')
							
					if row[5]=='present':
						frame_path = os.path.join(tmp_dir,dataset_name)
						frame_path = os.path.join(frame_path, 'frame_'+row[0]+'_'+row[2]+'_'+row[4]+'_'+str(second)+'.png')
		
						#log.info(frame_path)
						frame_name = 'frame_'+row[0]+'_'+row[2]+'_'+row[4]+'_'+str(second)+'.png'
						frame_name = frame_name [:-4]

						try:
							if os.path.isfile(frame_path):
								log.info('frame_path:')
								log.info(frame_path)
										
								img = Image.open(frame_path)
								base=300
								hpercent = (base / float(img.size[1]))
								wpercent = (base / float(img.size[0]))
											
								bounding_box = [float(row[6]),float(row[7]),float(row[8]),float(row[9])]
								cx1=int(((bounding_box[0])*img.size[0])*wpercent)
								cx2=int(((bounding_box[1])*img.size[0])*wpercent)-1
								cy1=int(((bounding_box[2])*img.size[1])*hpercent)
								cy2=int(((bounding_box[3])*img.size[1])*hpercent)-1
								img=img.resize((base,base), Image.ANTIALIAS)
								previous_video = video_id
																			
								out_file = BytesIO()
								img.save(out_file, format="png")
								out_file.seek(0)
								#label = [0, int(row[2]), 0, cx1 ,cy1, cx2, cy2]
								label = [int(row[2]), cx1 ,cy1, cx2, cy2]      
								sample_id = frame_name
			
								yield str(sample_id), {BONSEYES_PNG_IMAGE_TYPE: out_file}, {DIGIT_TYPE: label}
								#yield str(sample_id), {BONSEYES_PNG_IMAGE_TYPE: out_file}, {DIGIT_TYPE: label}
						except:
							print("Missing video")

					second+=1
					previous_video=video_id

def create (context: Context[DataSetEditor], images: str, labels:str):
	data = get_data (images, labels, context)
	write_dataset(context.data, data)
