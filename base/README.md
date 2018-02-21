Bonseyes dockerized training pipeline
================================================

Dependencies
---------------------------------------------

The following need to be installed:

   - Python 3
   - docker
   - docker-compose
   - python requests module

To use the GPU acceleration in the pipeline you also need:

   - Linux
   - NVidia binary drivers
   - nvidia-docker-compose
   - nvidia-docker

How to setup the client tool
--------------------------------

This code is usually installed in the folder `base` of the pipeline project.

The client tool is a python 3 program, you can get the user guide as follows:

    # setup the python path, not necessary if you use bin/bonseyes_client
    export PYTHONPATH="base/tools:base/common"

    # specify where the pipeline gateway can be reached, can be set in the 
    # command line too
    export BONSEYES_GATEWAY_HOST="localhost"
    export BONSEYES_GATEWAY_PORT="8000"

    python3 -m bonseyes_client --help
    
In *nix style environments you can use a script that also supports completion 
with the following:
 
    export PATH=$PATH:base/bin
    pip3 install argcomplete
    source bin/bonseyes_client.bash

You can then use the command directly:

    bonseyes_client --help

How to start the pipeline containers
-------------------------------------

You first need to build the pipeline containers with client tool 
using the following command line:

    python3 -m bonseyes_client build 

To run the pipeline you can then invoke the client tool as follows:

    python3 -m bonseyes_client start --gpu -p deployment_name
    
If your pipeline doesn't need the gpu you can remove --gpu parameter. To use the --gpu parameter you need
 to install nvidia-docker-compose and make sure the nvidia-docker daemon is accessible.

How to use the web interface
-----------------------------

Once the pipeline containers are started it is possible to access a web 
interface to control the pipeline. The web interface allows to control the
containers that perform the different steps of the training process.

The web interface is divided in four sections:

  - Task: this section contains information about the task for which the 
    pipeline is building a model.

  - Data: this section contains a list of all the data artifacts created by the
    pipeline and allows to create new artifacts.

  - Model: this section contains all the model related artifacts created by the
    pipeline and allows to create new artifacts.

  - Pipeline: this section allows to control the pipeline as a whole. Use this
    section to start a whole pipeline end-to-end (data import, model creation, 
    model benchmarking). Once the pipeline has run you can find the different
    artifacts created in the data and model sections.

To create a new artifact in any of the categories you need to press on the '+'
button. You then have to chose a name (that must be unique) and select the 
container that you want to use. Depending on the container you choose you will
have different parameters that need to be set. Check the pipeline documentation
for details about them.

Once the creation is started you can monitor the progress by clicking on the
refresh button (the circular arrow). You can get live log information by 
clicking on the down arrow near the artifact and then press refresh.

To download a completed artifact click on the download button (an arrow 
pointing towards a bar) in the corresponding row.

If the pipeline you loaded supports multiple tasks you can select which one you
want to operate on from the menu on the top-right of the screen.

How to use the client tool to control the pipeline
-----------------------------------------------------

Some examples using a dashboard (they work on the mnist example pipeline):

  - List the containers in the default pipeline:

      python3 -m bonseyes_client pipeline-container list-containers

  - Start a pipeline (assuming it doesn't require parameters):
   
      python3 -m bonseyes_client pipeline-container start --name run1

  - Check the logs of the run:

      python3 -m bonseyes_client pipeline-container run-log --name run1

  - Check the status of the run:

      python3 -m bonseyes_client pipeline-container run-status --name run1

  - List all artifacts on the container train_data_source:

      python3 -m bonseyes_client artifact-container --container train_data_source list-artifacts
      
  - List all parameters required to create a new artifact:

      python3 -m bonseyes_client artifact-container --container train_data_source list-create-params

  - Create a new artifact that takes two parameters:

      python3 -m bonseyes_client artifact-container --container train_data_source create-artifact --name test1 \
         --parameters '{"images_url": "http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz", '\
	              '"labels_url": "http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz"}'

  - Create a new artifact that takes two parameters and wait till completion while showing logs and force delete of
    an existing artifact with the same name:

      python3 -m bonseyes_client artifact-container --container train_data_source create-artifact --name test1 \
         --parameters '{"images_url": "http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz", '\
	              '"labels_url": "http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz"}' \
	     --wait-completed --log --force

  - Create a new artifact that takes two parameters and an input file (this doesn't work on the mnist pipeline):

      python3 -m bonseyes_client artifact-container --container train_data_source create-artifact --name test1 \
         --parameters '{"images_url": "http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz", '\
	              '"labels_url": "http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz"}' \
	     --input-file file1=path/to/some.zip file2=path/to/other.zip

  - Show the artifact creation log:

      python3 -m bonseyes_client artifact-container --container train_data_source artifact-log --name test1

  - Follow the artifact creation log:

      python3 -m bonseyes_client artifact-container --container train_data_source artifact-log --name test1 --follow

  - Show the status of the artifact:

      python3 -m bonseyes_client artifact-container --container train_data_source artifact-status --name test1

  - Download the artifact:

      python3 -m bonseyes_client artifact-container --container train_data_source export-artifact --name test1 --output-file test.zip
    
It is also possible to directly access a container (if its port has been mapped):

  - List all artifacts on the container mapped to port 8003:

      python3 -m bonseyes_client artifact-container --container 8003 list-artifacts

  - List all artifacts on the container mapped to http://127.0.0.1:8003:

      python3 -m bonseyes_client artifact-container --container http://127.0.0.1:8003 list-artifacts

To use a container without the starting the whole pipeline:

    python3 -m bonseyes_client run  -f containers/XXXX/Dockerfile --output-file test.out \
            --parameters '{"param1": "xxxxx"}' --input-file file_param=input_file.xxxx


Code structure
----------------

  - bin : the command line tool binary script

  - common : common code used by containers and client tools

  - code : common code used by containers

  - containers/base : base image to create a job container

  - containers/dashboard  : a container that provides a web-based dashboard
  
  - containers/visualization : a container that provides a web-based visualization tool to inspect the training
  
  - containers/gateway : a container that provides access to the pipeline containers from the host

  - doc : some guides about the pipeline environment

  - tools/bonseyes_client : client tool to control the pipeline

  - tools/code_format.py : code formatting script