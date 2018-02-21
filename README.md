Dockerized pipeline for MNIST model training
================================================

How to clone repository
-----------------------

This repository has submodules, to clone it use the following command:

    git clone git@bitbucket.org:bonseyes/wp3_pipeline_mnist.git --recursive

How to use the pipeline
-------------------------

For more information about the pipeline and tools refer to `base/README.md`.

Code structure
-------------------------

  - base (git submodule): generic container pipeline framework
   
  - components: reusable components to build the pipeline
  
     - bonseyes_training_base (git submodule): helper code to build a training pipeline
     
  - code : code shared by all containers
  
  - containers: all container images of the pipeline
  
     - mnist_import: import data from Lecun website in the pipeline
     
     - mnist_export: create a input and output tensors for the neural network being trained
     
     - mnist_train_validation_split: split a input/output tensors in learning tensors and validation tensors
     
     - mnist_training: build a MLP model to recognize handwritten digits
     
     - mnist_benchmarking: test a model against test data
     
     - mnist_pipeline: run whole the pipeline
     
     - mnist_lasagne_base: base image for mnist_training and mnist_benchmarking containing the lasagne training 
       framework
       
  - docker-compose-build.yml : compose file used to build images provided by the pipeline
  
  - docker-compose.yml : compose file used to start the pipeline
# My project's README
