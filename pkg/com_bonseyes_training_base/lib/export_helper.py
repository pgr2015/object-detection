#
# NVISO CONFIDENTIAL
#
# Copyright (c) 2017 nViso SA. All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") is the confidential and proprietary information
# owned by nViso or its suppliers or licensors.  Title to the  Material remains
# with nViso SA or its suppliers and licensors. The Material contains trade
# secrets and proprietary and confidential information of nViso or its
# suppliers and licensors. The Material is protected by worldwide copyright and trade
# secret laws and treaty provisions. You shall not disclose such Confidential
# Information and shall use it only in accordance with the terms of the license
# agreement you entered into with nViso.
#
# NVISO MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF
# THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. NVISO SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR
# DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
#
import logging as log
import os, sys
from typing import List, Callable, Tuple, Union, Optional
import zipfile


import logging
import numpy
import tempfile
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import lxml.etree as etree2
import requests
import subprocess
from PIL import Image
import io
from io import BytesIO
import time

import numpy
from multiprocessing import Queue

from .dataset_parallelize_process import read_datasets_and_process_samples
from com_bonseyes_base.formats.data.data_tensors.api import DataTensorsEditor
from com_bonseyes_base.formats.data.dataset.api import Datum, DataSetViewer
from com_bonseyes_base.lib.api.tool import Context
from distutils.log import Log

ProcessingFunction = Callable[[Datum], Tuple[numpy.ndarray, numpy.ndarray]]


def sample_processor(process_sample_fun: ProcessingFunction, dataset_id: Optional[int],
                     datum: Datum, output_queue: Queue):

    exported_data = process_sample_fun(datum)

    output_queue.put([dataset_id, datum.sample.name, exported_data])


        
def write_tensor(context: Context[DataTensorsEditor],editor: DataTensorsEditor, class_names: List[str],
                 write_outputs: bool, tensors_queue: Queue,
                 input_dimensions: List[Tuple[str, int]],
                 output_dimensions: List[Tuple[str, int]],
                 input_type: str,
                 output_type: str):
    

    logging.info("Started write tensor process with pid %d" % os.getpid())


    with editor:

        # initialize the data tensor
        logging.info("Initializing output tensors")
        editor.initialize(class_count=len(class_names),
                          input_dimensions=input_dimensions,
                          output_dimensions=output_dimensions,
                          input_data_type=input_type,
                          output_data_type=output_type)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            with context.data.edit_content() as output_file:
        
                image_name_bonseyes = '_data_com.bonseyes.png_image'
                #input_artifact="/volumes/data/"
                link_test_file_path = tmp_dir+'/trainval.txt'
                #link_test_file_path = tmp_dir+'/trainval.txt'
                
                class_list = ["person", "bird", "bicycle", "boat", "bus", "bear", "cow", "cat", "giraffe", "potted", "horse", "motorcycle", "knife", "airplane", "skaterboard", "train", "truck", "zebra", "toilet", "dog", "elephant", "umbrella", "none_of_the_above", "car"]
    
        
                with open(link_test_file_path, 'w') as f:
                    
                    while True:
         
                        next_item = tensors_queue.get()

                        # if we receive a new item we schedule it for write
                        if next_item is not None:
         
                            dataset_id, sample_name, exported_data = next_item
                            
                            log.info(dataset_id)
                            log.info(sample_name)
                        
                            # This sample should be skipped
                            if exported_data is None:
                                skipped += 1
                                continue
                            
                            log.info(exported_data[1])
                
                            #input_sample = numpy.zeros(exported_data[0], dtype=input_type)
                            input_sample = exported_data[0]
                            #output_sample = numpy.zeros(exported_data[1], dtype=output_type)
                            output_sample = exported_data[1]
                            
                            sample_dir = os.path.join(tmp_dir, sample_name)
                            #sample_dir = os.path.join(tmp_dir, sample_name)
                            #os.makedirs(sample_dir)
            
                            output_sample_path = sample_dir+image_name_bonseyes
            
                            im = Image.fromarray(input_sample.astype('uint8'), 'RGB')
                            im.save(output_sample_path,'PNG')
                            annotations = sample_name #value['annotations'].get('com.bonseyes.example.youtubebb.digit_label')
                            annotationElement = ET.Element('annotation')
                            folderElement = ET.SubElement(annotationElement, 'folder')
                            folderElement.text = tmp_dir+sample_name
                            log.info(folderElement.text)
                            filenameElement = ET.SubElement(annotationElement, 'filename')
                            filenameElement.text = sample_name+"com.bonseyes.png_image"
                            log.info(filenameElement.text)
                            sizeElement = ET.SubElement(annotationElement, 'size')
                            widthElement = ET.SubElement(sizeElement, 'width')
                            widthElement.text = str(300)
                            heightElement = ET.SubElement(sizeElement, 'height')
                            heightElement.text = str(300)
                            depthElement = ET.SubElement(sizeElement, 'depth')
                            depthElement.text = str(3)
            
                            objectElement = ET.SubElement(annotationElement, 'object')
                            nameElement = ET.SubElement(objectElement, 'name')
                            bndboxElement = ET.SubElement(objectElement, 'bndbox')
                            xminElement= ET.SubElement(bndboxElement, 'xmin')
                            yminElement= ET.SubElement(bndboxElement, 'ymin')
                            xmaxElement= ET.SubElement(bndboxElement, 'xmax')
                            ymaxElement= ET.SubElement(bndboxElement, 'ymax')
                            xminElement.text = str(int(output_sample[0,1]))
                            yminElement.text = str(int(output_sample[0,2]))
                            xmaxElement.text = str(int(output_sample[0,3]))
                            ymaxElement.text = str(int(output_sample[0,4]))
                            nameElement.text = str(class_list[int(output_sample[0,0])])
            
                            #path = os.path.join(tmp_dir, sample_name+".xml")
                            path = os.path.join(tmp_dir, sample_name+".xml")
                            myfile = open(path, "w")
                            myfile.write(ET.tostring(annotationElement).decode("utf-8"))
                            myfile.close()
                            link_string = sample_name+image_name_bonseyes +" "+sample_name+".xml\n"
                            log.info(tmp_dir)
                            log.info(sample_name+"/"+image_name_bonseyes +" "+sample_name+".xml\n")
                            f.write(link_string)
                            
                        if next_item is None:
                            logging.info("Received shutdown")
                            break
    
                    f.flush()
                    #link_file.close()
                    f.close()
                    #mapfile=data_root_dir+"/"+dataset_name+"/labelmap_youtubebb.prototxt"
                #time.sleep(20)
                download("http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/training/labelmap_youtubebb.prototxt", os.path.join(tmp_dir, "labelmap_youtubebb.prototxt"))
                download("http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/training/create_annoset.py", os.path.join(tmp_dir, "create_annoset.py"))
                download("http://161.67.219.121/BONSEYES_Reference_Datasets/YoutubeBB/training/convert_annoset", os.path.join(tmp_dir, "convert_annoset"))
                  
                os.chmod(os.path.join(tmp_dir, "convert_annoset"), 0o777)
                redo = 0
                root_dir = tmp_dir
                #root_dir = input_artifact
                data_root_dir = tmp_dir
                dataset_name = "youtube-bb"
        
                mapfile= os.path.join(data_root_dir, "labelmap_youtubebb.prototxt")
                testFile = tmp_dir
        
                anno_type = "detection"
                db = "lmdb"
                min_dim = 0
                max_dim = 0
                width = 0
                height = 0
        
                extra_cmd = "--encode-type=png"# --encoded"
                if redo:
                    extra_cmd= extra_cmd +" --redo"
        
                log.info(extra_cmd)
                test_trainval = ["test", "trainval"]
        
                element = "trainval"
                elementxt = "datatest.txt"

                log.info (output_file)
        
                cmd = ['python3', root_dir+"/"+"create_annoset.py", "--anno-type="+anno_type, "--label-map-file="+mapfile, "--min-dim="+str(min_dim), "--max-dim="+str(max_dim), "--resize-width="+str(width), "--resize-height="+str(height),"--check-label", extra_cmd, '--encoded', '--redo', data_root_dir, os.path.join(testFile, element+".txt"), os.path.join(output_file[:-5], dataset_name+"_"+element+"_"+db), "examples/"+dataset_name]
                log.info(cmd)
    
                process = subprocess.Popen(cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                output, errors = process.communicate()
                log.info( output)
                log.info( errors)
                log.info ('van los path')
                path1 = os.path.join(output_file[:-5], dataset_name+"_"+element+"_"+db+"/data.mdb")
                log.info (path1)
                path2 = os.path.join(output_file[:-5], dataset_name+"_"+element+"_"+db+"/lock.mdb")
                log.info (path2)

                os.remove(output_file)

                with zipfile.ZipFile(output_file, 'a') as z:
                    z.write(path1, arcname=dataset_name+"_"+element+"_"+db+'/data.mdb')
                    z.write(path2, arcname=dataset_name+"_"+element+"_"+db+'/lock.mdb')


            
            
            
def download(url, output_file):

    if os.path.exists(output_file):
        log.info('Output file already exists')

    else:
        ret = requests.get(url, stream=True)

        if ret.status_code != 200:
            raise Exception('Unable to file (error code %d)' % ret.status_code)

    with open(output_file, 'wb') as fp:
        for chunk in ret.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fp.write(chunk)
    
    log.info("Downloaded %d bytes", os.path.getsize(output_file))   
             

def write_classification_tensor(context: Context[DataTensorsEditor],dataset_viewers: Union[DataSetViewer, List[DataSetViewer]],
                                input_dimensions: List[Tuple[str, int]],
                                input_type: str,
                                class_names: List[str],
                                export_data_types: Union[str, List[str]],
                                process_sample_fun: ProcessingFunction,
                                editor: DataTensorsEditor,
                                output_dimensions: List[Tuple[str, int]]=None,
                                output_type: str=None,
                                write_outputs: bool=True,
                                workers_count: int=1):

    logging.info("Starting writing")

    def bound_processing_fun(dataset_id: Optional[int], datum: Datum, output_queue: Queue):
        sample_processor(process_sample_fun=process_sample_fun,
                         dataset_id=dataset_id,
                         datum=datum,
                         output_queue=output_queue)

    def bound_write_fun(queue: Queue):
        write_tensor(context=context, editor=editor,
                     class_names=class_names,
                     write_outputs=write_outputs,
                     tensors_queue=queue,
                     input_dimensions=input_dimensions,
                     output_dimensions=output_dimensions,
                     input_type=input_type,
                     output_type=output_type)

    read_datasets_and_process_samples(dataset_viewers, export_data_types, workers_count,
                                      bound_processing_fun, bound_write_fun)

    logging.info("Tensor written")
