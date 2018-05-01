Tool Manifests
==============

.. contents::

Overview
--------

The tool manifest file is a :doc:`YAML <yaml>` file that describes how to instantiate and use a tool. The
manifest file contains a mapping described in the next section.

Top level structure
-------------------

The manifest is a mapping containing the following keys:

  - `description`: (required) Human readable description of the tool described in the manifest
  - `output`: (required) information about the output format of the tool (see `Output section`_)
  - `image`: (required) instructions on how to instantiate the tool (see `Image section`_)
  - `actions`: (required) mapping of action names to action descriptions (see `Actions section`_)

Example:

.. code-block:: yaml

    description: "Sample tool"
    output:
       ...
    image:
       ...
    actions:
       ...


Output section
--------------

The output section of the manifest is a mapping with a required key `data_format`, that contains the name of the format
in reverse dotted notation of the data in the artifacts create by this tool.

Example:

.. code-block:: yaml

    output:
      data_format: com.bonseyes.example.output.1.0


Image section
-------------

The image section of the manifest is a mapping with a required key `image_type`.

This key defines the rest of the mapping and can have one of the following values:

  - `dockerfile`:  the tool is instantiated by first building an image using a Dockerfile
  - `docker-image`: the tool is instantiated from an existing Docker image

When the image type is dockerfile then the following keys are available:

  - `dockerfile`: (required) this entry can take two types of values:

        - A path to a single Dockerfile file
        - An array of multiple paths to Dockerfile files

    In the first case the image for the tool is built using the file specified.

    In the second case Docker is first used to create an image using the first Dockerfile in the list. Then
    once this is completed and tagged a second image is built using the the second Dockerfile.

    For the second image a build parameter `BASE_IMAGE` is injected during the image build. If the second Dockerfile
    starts with:

    .. code-block:: Dockerfile

        ARG BASE_IMAGE
        FROM ${BASE_IMAGE}

    then the second image is effectively built as an extension of the first image. The process is repeated once for
    each Dockerfile in the list. The last image generated is then used a the image of the tool.

  - `name`: (required) name of the docker image that will be created

  - `base_image`: (optional) description of the image from which this image is built. This base image is build before
    the image is built and its name is injected as a build var BASE_IMAGE during the build process.

The value corresponding to this key can be either:

  - A pointer to another tool, in this case the value is a mapping containing only one key, `manifest`, that is a path
    to a tool manifest containing an image section.

  - A description of an image as described in this section of the document, such as a `dockerfile` or `docker-image`.

When the image type is `docker-image` then the following keys are available:

  - `name`: (required) name of the docker image that should be used

  - `tag`: (optional) tag of the image to use

  - `registry`: (optional) name of the registry containing the image. It can be a full name (without trailing slash) or
    a boolean value. When set to true the image is pulled from the official name docker hub, when set to false an image
    local to the docker engine is used.

Example of an image built from a Dockerfile and that use a default base image:

.. code-block:: yaml

    image_type: dockerfile
    name: com.bonseyes.example.tools.sample
    dockerfile: ./tools/sample/Dockerfile
    base_image:
        image_type: docker-image
        name: com.bonseyes.base.cpu


Example of an image downloaded from Docker Hub:

.. code-block:: yaml

    image_type: docker-image
    name: com.bonseyes.example.tools.sample
    registry: true
    tag: latest

Actions section
---------------

This section of the manifest file defines all the actions that are supported by the tool. Every tool must support at
least one action create that creates an artifact. The mapping keys are the names of the actions supported by the tool,
the corresponding values are an mapping containing all the details about the action, such as description, parameters,
etc.

Below you can find an example of an action section that defines the mandatory `create` action and an additional action
`some_other_action`:

.. code-block:: yaml

    actions:
        create:
            < description of the action >
        some_other_action:
            < description of the action >

The description of an action has the following keys:

  - `description`: (optional) human readable description of the action

  - `parameters`: (required) the parameters of the action (see :ref:`below <parameters>`)

  - `metrics`: (optional) description of the metrics of the action (see :ref:`below <metrics>`)

.. _parameters :

The parameters of the action are described using a mapping containing the following keys:

  - `label`: (optional) human readable description of the parameter

  - `type`: (required) type of parameter,  one choice of the following: string, url, resource, json, archive (see the
    section on values for more information about the meaning of each option)

  - `data_format` (optional) defines of the format of the data pointed by the parameter (for archive and resource
    parameters). The type of the parameter must be resource if the format extends com.bonseyes.format.blob and archive
    if the format extends com.bonseyes.format.directory.

.. _metrics :

The description of metrics of an action is a mapping, each key defines the name of the metric while the value is a
mapping with the following keys:

  - `type`: (required) the type of the metric in reverse dotted notation.

  - `label`: (optional) a human readable description of the metric

.. todo::

    Need to improve clarity of this section

Example of a action description:

.. code-block:: yaml

    label: "Action description"
    metrics:
      metric1:
         type: com.bonseyes.progress.0.1
        label: "Action progress"
    parameters:
      parameter1:
        type: string
        label: "Parameter 1"
      parameter2:
        type: resource
        label: "Parameter 2"
        data_format: com.bonseyes.example.format.0.1