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

import requests
from PIL import Image
import numpy as np
from io import BytesIO

import logging as log

from bonseyes_youtubebb import DIGIT_TYPE
from bonseyes_training_base import BONSEYES_PNG_IMAGE_TYPE


def download(url, output_file):

    if os.path.exists(output_file):
        raise Exception('Output file already exists')

    ret = requests.get(url, stream=True)

    if ret.status_code != 200:
        raise Exception('Unable to file (error code %d)' % ret.status_code)

    with open(output_file, 'wb') as fp:
        for chunk in ret.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fp.write(chunk)


def get_data(images_url,labels_url):

    with tempfile.TemporaryDirectory() as tmp_dir:

        images_file = os.path.join('/datasetfiles', images_url.split('/')[-1])
        
        if not os.path.exists(images_file):
            log.info("Downloading %s to %s" % (images_url, images_file))
            download(images_url, images_file)
            log.info("Downloaded")
        else:
            log.info("Using an existing file")
            
        labels_file = os.path.join('/datasetfiles', labels_url.split('/')[-1])
        
        if not os.path.exists(labels_file):
            log.info("Downloading %s to %s" % (labels_url, labels_file))
            download(labels_url, labels_file)
            log.info("Downloaded")
        else:
            log.info("Using an existing file")
        
        #samples_data = []
        samples_names = []
        
        with tarfile.open(images_file, 'r') as tar:
            
            for member in tar.getmembers():

                file = member.name
                file = os.path.normpath(file)

                if (not file.endswith('.png')):
                    continue

                sample_id = os.path.basename(file)[:-4]
                
                #sample_data = tar.extractfile(member) #,'/data')
                #samples_data.append(sample_data)
                samples_names.append(sample_id)
                tar.extract(member, '/datasetfiles')
                
                #===============================================================
                # label=0
                # yield str(sample_id), {BONSEYES_PNG_IMAGE_TYPE: sample_data}, {DIGIT_TYPE: label}
                #===============================================================
                
                         
                    
        
        csv_name='/datasetfiles/youtube_boundingboxes_detection_train.csv'
        with open(csv_name, 'r') as csvfile:
            reader = csv.reader(csvfile)
            previous_video = str('')
            second=0
            
            for row in reader:
                
                video_id = row[0]+'+'+row[2]+'+'+row[4]
                #video_id = row[0]
                                
                if  video_id != previous_video:
                    second=0
                 
                if row[5]=='present':    
                    frame_path = '/datasetfiles/frame_'+row[0]+'_'+row[2]+'_'+row[4]+'_'+str(second)+'.png'
                    frame_name = 'frame_'+row[0]+'_'+row[2]+'_'+row[4]+'_'+str(second)+'.png'
                    frame_name = frame_name [:-4]
                    
                    try:
                        if os.path.isfile(frame_path):
                             #f = open('/datasetfiles/frame_'+row[0]+'_'+row[2]+'_'+row[4]+'_'+str(second)+'.txt','a')
                            img = Image.open(frame_path)
                            base=416;
                            hpercent = (base / float(img.size[1]))
                            wpercent = (base / float(img.size[0]))
                            
                            bounding_box = [float(row[6]),float(row[7]),float(row[8]),float(row[9])]
                            cx1=int(((bounding_box[0])*img.size[0])*wpercent)
                            cx2=int(((bounding_box[1])*img.size[0])*wpercent)
                            cy1=int(((bounding_box[2])*img.size[1])*hpercent)
                            cy2=int(((bounding_box[3])*img.size[1])*hpercent)
                            img=img.resize((base,base), Image.ANTIALIAS)
                            #f.write(str(row[2])+' '+str(-1)+' '+str(-1)+' '+str(0.0)+' '+str(format(cx1, '.2f'))+' '+str(format(cy1, '.2f'))+' '+str(format(cx2, '.2f'))+' '+str(format(cy2, '.2f'))+' '+str(0.0)+' '+str(0.0)+' '+str(0.0)+' '+str(0.0)+' '+str(0.0)+' '+str(0.0)+' '+str(0.0) +' '+str(0.0)+'\n')
                            previous_video = video_id
                            #f.close()
                                                        
                            out_file = BytesIO()
                            img.save(out_file, format="png")
                            out_file.seek(0)
                            
                            label = [int(row[2]), cx1, cx2 ,cy1, cy2]
                            
                            sample_id = os.path.basename(file)[:-4]
                            
                            yield str(sample_id), {BONSEYES_PNG_IMAGE_TYPE: out_file}, {DIGIT_TYPE: label}

            
                            
                            #===================================================
#                             with tarfile.open(images_file, 'r') as tar:
#             
#                                 for member in tar.getmembers():
# 
#                                     file = member.name
#                                     file = os.path.normpath(file)
# 
#                                     if (not file.endswith('.png')):
#                                         continue
# 
#                                     sample_id = os.path.basename(file)[:-4]
#                                     if sample_id == frame_name:
#                                         label = [int(row[2]), cx1, cx2 ,cy1, cy2]
#                                         sample_data = tar.extractfile(member) #,'/data')
#                                         
#                                         yield str(sample_id), {BONSEYES_PNG_IMAGE_TYPE: sample_data}, {DIGIT_TYPE: label}
#                                         break


                            #===================================================
                            # idx=0
                            # for sample_data in samples_data:
                            #     sample_name = samples_names[idx]
                            #     
                            #     if  sample_name == frame_name:
                            #         log.info(frame_name)
                            #         log.info('sample name')
                            #         log.info(sample_name)
                            #                                             
                            #         sample_id=sample_name
                            #         label = row[2] #, cx1, cx2 ,cy1, cy2]
                            #         
                            #         yield str(sample_id), {BONSEYES_PNG_IMAGE_TYPE: sample_data}, {DIGIT_TYPE: label}
                            #         
                            #     idx=idx+1  
                            #===================================================

                            
                    except:
                         print("Missing video")
      
                second+=1
                #previous_video=video_id     
        

                 
                 

