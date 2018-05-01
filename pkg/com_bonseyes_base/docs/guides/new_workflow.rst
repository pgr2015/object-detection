.. highlight:: shell

Developing new workflows
========================

Overview
--------

The process to develop a new workflow is typically the following:

  1) Create a new project directory under git control
  2) Download all the packages containing the manifests of the tools that are needed in the pkg subdirectory
  3) Write a workflow YAML file

Example
-------

This example shows how to create a pipeline that uses a few tools.

Assume that `$PROJECT_URL` points to an empty git repository. The first step is to create a local project directory::

    git clone $PROJECT_URL example-project

    cd example-project

To configure a project you need to include all packages providing the tools will be used in the workflow and their
dependencies. A list of packages is available on Bitbucket.

All projects must contain the package com.bonseyes.base with the framework code::

    git submodule add \
        git@bitbucket.org:bonseyes/wp3-com.bonseyes.base.git \
        pkg/com_bonseyes_base

You can then add other tools depending on your workflow, for instance::

    git submodule add \
        git@bitbucket.org:bonseyes/wp3-com.bonseyes.inference.git \
        pkg/com.bonseyes.inference

It is now possible to create a workflow file for instance in `workflows/example.yml`, for details on the language refer
to the reference sections later in this document.

.. code-block:: yaml

    # this is the description of the workflow
    description: "Performs a Caffe inference"

    # the following section lists all the inputs of the workflow
    # in this case one parameter: the input data on which to perform
    # the inference
    parameters:

      input_data:
         label: "HDF5 file with input data"
        type: resource

    # the following section lists all the outputs of the workflow, in
    # this case just one output called "inference" that will contain
    # the inference results
    outputs:
       inference:
         label: "Inference results"

    # the following section lists all the tools that are used
    # in this case one instance of the caffe inference tool named
    # caffe inference
    workers:

       # this defines a worker name caffe_inference
       # the tool is instantiated using the manifest information
      caffe_inference:
        manifest: ./pkg/com.bonseyes.inference/tools/caffe_inference/manifest.yml

    # the following section lists all the steps of the workflow
    # in this case only one step that performs the inference
    steps:

      - description: Perform inference with caffe

        worker: caffe_inference    # this is the worker
                                   # that will be used

        output: inference          # the artifact produced by this
                                   # step is saved as the output of the workflow

        parameters:                # the parameters that are passed to the tool

          model_architecture: http://example.com/model.prototxt

          model_weights: http://example.com/weights.caffeweights

          dataset:                      # the workflow parameter
                                        # is forwarded to the tool
              type: workflow-parameter
              name: input_data
