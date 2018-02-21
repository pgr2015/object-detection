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

from bonseyes_containers.pipeline_api import create_artifact_if_not_complete


def execute_run(artifact, input_data, input_files):

    name = input_data['name']

    train_dataset = create_artifact_if_not_complete('youtubebb_import', name + '_train_dataset',
                                                    {'images_url': 'http://bonseyes.uclm.es/BONSEYES_Reference_Datasets/YoutubeBB/training/imagesyoutubeBB_T.tar.gz',
                                                     'labels_url': 'http://bonseyes.uclm.es/BONSEYES_Reference_Datasets/YoutubeBB/training/labelsyoutubeBB_T.tar.gz'})
    
    train_dataset.wait_for_completed()

    benchmark_dataset = create_artifact_if_not_complete('youtubebb_import', name + '_benchmark_dataset',
                                                    {'images_url': 'http://bonseyes.uclm.es/BONSEYES_Reference_Datasets/YoutubeBB/testing/imagesyoutubeBB_B.tar.gz',
                                                     'labels_url': 'http://bonseyes.uclm.es/BONSEYES_Reference_Datasets/YoutubeBB/testing/labelsyoutubeBB_B.tar.gz'})
    
    benchmark_dataset.wait_for_completed()

    train_tensor = create_artifact_if_not_complete('youtubebb_export', name + '_train_tensor',
                                                   {'input-url': train_dataset.url})

    train_tensor.wait_for_completed()

    benchmark_tensor = create_artifact_if_not_complete('youtubebb_export', name + '_benchmark_tensor',
                                                       {'input-url': benchmark_dataset.url})
    benchmark_tensor.wait_for_completed()

    training_set = create_artifact_if_not_complete('youtubebb_train_validation_split', name + '_trainingset',
                                                   {'input-url': train_tensor.url})
    training_set.wait_for_completed()

    model = create_artifact_if_not_complete('youtubebb_training', name + '_model',
                                            {'training-set': training_set.url})
    model.wait_for_completed()

    benchmark = create_artifact_if_not_complete('youtubebb_benchmarking', name + '_benchmark',
                                                {'model': model.url, 'tensor': benchmark_tensor.url})
    benchmark.wait_for_completed()
