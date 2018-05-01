.. highlight:: shell

Setup
=====

The client tool is a python code. There exist two execution options:

 1) Local execution: Run the CLI tool on the host system
 2) Dockerized execution: Run the CLI tool inside a container

The first solution can be run on a host that has only docker installed,
the second requires Python and some dependencies on the host.

Prerequisites
-------------

To run this code you need:

  - git
  - bash or similar shell
  - Docker 17.12 or later

Installing the code
-------------------

The workbench can be downloaded as follows::

    git clone --recursive git@bitbucket.org:bonseyes/wp3-project-workbench.git workbench

Using be-admin in a docker container
------------------------------------

To build the docker image with be-admin run the following command::

    cd workbench

    ./com_bonseyes_base/scripts/build_beadmin_container.sh

You can now use the shell script `docker-be-admin` in `pkg/com_bonseyes_base/bin/` that starts the docker container::

    PATH=$PATH:$(pwd)/pkg/com_bonseyes_base/bin/

    docker-be-admin --help

This command is equivalent to `be-admin`, the only restriction is that it can access only files in the
current directory.
 
Using be-admin on the local host
--------------------------------

To be able to run be-admin locally you need the following:

   - Python 3.5
   - pip
   - virtualenv

To setup for local execution you first need to create a virtualenv::

    virtualenv -p python3 be
     
Then you need to activate the local environment::

    source be/bin/activate
    
Then you need to install the depenedencies::

    pip3 install -r pkg/com_bonseyes_base/images/cli/requirements.txt

Finally you need to add the CLI tool to PATH::

    PATH=$PATH:$(pwd)/pkg/com_bonseyes_base/bin
