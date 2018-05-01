.. highlight:: shell

Developing a new tool
=====================

Introduction
------------

To develop a tool using the default docker implementation you need to create the following files:

  - A `Dockerfile` file that describes the docker image containing the tool
  - A `manifest.yml` file that describes the tool interface
  - An `actions.py` file that implements the actions provided by the tool

Typically the tool code is organized in a package. Building and testing of the tool is performed in a top level project
that includes the package and all the dependencies. The `Dockerfile` of the tool is written assuming that it is built
at the top of this directory.

How to start a new project
--------------------------

Assume that `$PROJECT_URL` points to an empty git repository that will contain the top level testing project and
that `$PACKAGE_URL` points to a second empty git repository for a new package with name `$PACKAGE_NAME` that will
contain the tool with name `$TOOL_NAME` that we want to develop.

The first step is to create the new top level project::

    git clone $PROJECT_URL myproject

    cd myproject

Then it is necessary to add the framework code::

    git submodule add \
        git@bitbucket.org:bonseyes/wp3-com.bonseyes.base.git \
        pkg/com_bonseyes_base

and add a submodule where the tool will be located::

    git submodule add $PACKAGE_URL pkg/$PACKAGE_NAME

Finally add the directory for tool::

    mkdir -p pkg/$PACKAGE_NAME/tools/$TOOL_NAME

You can then commit the changes to your package::

    cd pkg/$PACKAGE_NAME
    git checkout master
    git add .
    git commit -m "Added tool $TOOL_NAME"
    git push origin
    cd ../..

And finally commit the changes to the top level tool::

    git add .
    git commit -m "Initial import"
    git push origin

Example
-------

Assume for instance that you want to create a new tool `example_tool` that depends on  packages
`com.example.dependency1` and `com.example.dependency2`.

The structure of the project should be the following:

    - Root of the tool development project (git repository root)
        - pkg
            - com_bonseyes_base (git submodule root)
            - com_example_package ( git submodule root )
                - tools
                    - example_tool
                        - Dockerfile
                        - actions.py
                        - manifest.yml
                - images
                - plugins
                - lib
            - com_example_dependency1 ( git submodule root )
            - com_example_dependency2 ( git submodule root )
        - workflow
            - test_example_tool.yml

The `Dockerfile` would be similar to this:

.. code-block:: Dockerfile

    FROM ubuntu:xenial

    RUN pip3 install h5py

    ADD pkg/com.example.package/lib /app
    ADD pkg/com.example.dependecy1/lib /app
    ADD pkg/com.example.dependecy2/lib /app
    ADD pkg/com.example.package/tools/example_tool /app

Assume the tool can create artifacts using one parameter `input_url`, the tool can be instantiated by building a
`Dockerfile`. The `manifest.yml` file that defines the tool interface would then be the following:


.. code-block:: yaml

    description: "Example tool"
    output:
      data_format: com.bonseyes.data.blob
    image:
      image_type: dockerfile
      name: com.example.example_tool
      dockerfile:
        # tool specific code
        - ./pkg/com_example_package/tools/example_tool/Dockerfile
        # framework code
        - ./pkg/com_bonseyes_base/images/base/Dockerfile

    actions:
      create:
        parameters:
            input_url:
              label: "Input data set"
              type: resource
              data_format: com.bonseyes.data.data-tensor

Assume the output of the tool is a file with containing the string `Test`. The `actions.py` file for this tool would be:

.. code-block:: python

    def create(context: Context, input_url: str):
        with context.data.edit_content() as output_file:
               with open(output_file, 'w') as fp:
              fp.write('Test')

In this example the artifact will just contain the string `Test`.

Patterns
--------

Efficient builds
^^^^^^^^^^^^^^^^

During development it is possible to speed up the build by decomposing the `Dockerfile` of the tool in two files. This
technique makes sure the Docker caching mechanism is used as much as possible by moving the instructions that change
most likely the image as late as possible in the build process.
The first file, named Dockerfile-base contains all the dependencies and the second part, named `Dockerfile` contains
only the tool code itself. The image section of the manifest then should be modified as follows:

.. code-block:: yaml

    image:
      image_type: dockerfile
      name: com.example.example_tool
      dockerfile:
        # tool dependencies (almost never changes)
        - ./pkg/com_example_package/tools/example_tool/Dockerfile-base
        # framework code (changes seldom)
        - ./pkg/com_bonseyes_base/images/base/Dockerfile
        # tool specific code (changes frequently)
        - ./pkg/com_example_package/tools/example_tool/Dockerfile

Debugging
---------

Debugging with PyCharm and PyDev
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to debug the code in the containers using pydev (or PyCharm Professional). To do so you need to set two
variables in the environment of the tool instances to instruct the code of the tool to connect to the debugger and to
describe the mapping between files in the tool container and on your development machine.

The simplest way to enable debugging is to create an execution config as follows:

.. code-block:: json

    {
      "application_config" : {
        "run_opts": {
          "environment" : {
            "PYDEVD_DEBUGGER": "192.168.10.86:5678",
            "PATHS_FROM_ECLIPSE_TO_PYTHON":
              "[[\"/host/example.py\",\"/instance/example.py\"]]"
          }
        }
      }
    }

The `PYDEVD_DEBUGGER` variable is used to define the address where the debugger is listening.
The `PATHS_FORM_ECLIPSE_TO_PYTHON` is used to define the mapping between paths on the host and in the container to
allow to set breakpoints.

Debugging with gdb
^^^^^^^^^^^^^^^^^^

It is possible to connect gdb to a running container as follows:

First find the container ID using ::

    be-admin status [name of the execution]

Then connect to the container::

    docker exec -ti containerid bash

In install in the container the debugger::

    apt-get update
    apt-get install gdb python3-dbg

Finally on the host as root::

    nsenter -t [external pid of uwsgi] -m -p gdb -p [internal pid of uwsgi]
