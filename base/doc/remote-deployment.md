Remote Deployment Guide
=========================

Overview
---------

It is possible to run a docker compose script on a remote machine. This can be useful for instance when the machine has to be
shared among many people or hosted on a remote location.

To work in this setup it is necessary to:

  1. Make the docker daemon on the server listen on a tcp port

  2. Forward docker daemon and nvidia-docker-daemon using ssh from the workstation

  3. Specify the host to be used when calling docker-compose



Setup a docker server
---------------------

The host needs to have NVidia CUDA drivers, Ubuntu 16 LTS and ideally persistent storage.

  1. On the server install Docker CE from the official website (see https://docs.docker.com/engine/installation/linux/ubuntu/)

  2. Install a firewall on the server and restrict outside access to all ports except ssh.
  
  2. Install and configure nvidia-docker (see https://github.com/NVIDIA/nvidia-docker). Make sure you test nvidia-smi in a 
     container as explained in the guide.

  3. Make sure the user that will access remotely the server is in the group docker.

  4. Install and configure ssh for remote access.


Warning: this setup assumes that all code on the docker host is trusted.


Use the docker host from a workstation
----------------------------------------

  1. Install docker CE from Docker official website

  2. Install python3 and pip

  3. Install with pip docker-compose and nvidia-docker-compose

  4. Connect with ssh to the docker server with the following local port forwardings:
      
      - 2375:/var/run/docker.sock (this is used to connect to the docker daemon on the server)
      - 3476:127.0.0.1:3476 (this is used to connect to the nvidia docker daemon on the server)

     For example on Linux or MacOSX use the following command line:

     	ssh admin@1.2.3.4 -L 2375:/var/run/docker.sock -L 3476:127.0.0.1:3476

     where 1.2.3.4 is the host that is running docker and admin is the user on the server.

  5. When invoking the command `nvidia-docker-compose`, `docker-compose` or `docker` add the -H parameter as follows:

    nvidia-docker-compose -H tcp://127.0.0.1:2375 -p XXXX up --build

     For instance you could test the setup by creating a file `docker-file.yml`:

    version: '3'
    services:
        nvidia-smi:
	    image: nvidia/cuda
	    command: nvidia-smi

     and execute it with the following command:

    nvidia-docker-compose -H tcp://127.0.0.1:2375 -p test_nvidia up

     The command should show the list of GPUs in the server.

  6. To access the ports exposed by the containers it is necessary to set up appropriate ssh port forwardings
