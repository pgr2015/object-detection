Developer Guide
===================

Overview
-------------

This framework allows to create data processing pipelines that train models for a specific task. Each project can 
contain one or more pipelines that may share some of the containers.
  
A **task** is defined as following:

  - `name`: a reverse domain name notation that uniquely identifies the task  
  - `description`: a textual description of the task
  - `output`: description of the output of the pipeline
  - `constraints`: a textual description of the functional/non-functional constraints that the model should satisfy
  - `archives`: a textual description with a list of archives that contain training data for the the task
  - `evaluation_criterias`: a textual description of the evaluation criterias
  - `cost_function`: a cost function used for training
  - `evaluation_dataset`: a textual description of the data to be used to test the model
  
Each pipeline creates models for a specific task. There can be multiple pipelines for the same task.

The pipeline is composed by a set of docker containers that can process the data and perform the training. Additionally 
the pipeline contains two auxiliary containers: 

  - The **pipeline container** that is responsible for coordinating the other containers
  - The **visualization container** that allows to inspect the metrics exported by other containers.
 
The project always contains two additional containers: 

  - A **dashboard** that allows to control the the pipelines and containers of the project
  - A **gateway** that acts as reverse-proxy so that all containers can be accessed from a single port on the host 

The typical containers of a pipeline are:
 
  - an **import container** that loads that from an archive and stores it in a standardized form
  - a **processing container** that creates a pre-processed view of the raw data loaded by the import container
  - an **export container** that takes the pre-processed view an creates tensors suituable as input/outputs of the 
    neural network.
  - a **training set creation container** that create splits the tensor data of the export container in 
    training/validation sets for the training
  - a **training container** that creates a model
  - a **benchmarking container** that tests the performance of the model according to the task evaluation criterias
   
Each containers used by the pipeline can be used to create artifacts of some type. Each container can produce one 
specific type of output. The artifacts created by the container are stored in a volume mounted by the container and 
can be downloaded on request by other containers. The artifact creation has different parameters that depend on the
container. The creation of artifacts is asynchronous, whoever requests the creation of an artifact doesn't need to
wait the completion of the request.

The pipeline container can be used to run the whole pipeline. When running a pipeline this container issues requests
to the other containers in a given order so that at the end of the run all required data-processing has been done 
and the desired model has been created. Like for artifacts, runs are executed asynchronously by the pipeline container.
   
Operation of all containers can be monitored using the web based dashboard or a python client. Containers can export
 metrics during artifact creation that can be inspected in real time with the visualization container.

Code organization
------------------

A project consists of the following parts:

  - the `base` directory that contains the base tooling and code
  - the `containers` directory that contains all the task specific containers
  - the `components` directory that contains all re-usable components for assembling the pipeline
  - the `docker-compose-build.yml` file that declares how to build the container images of the pipeline
  - the `docker-compose.yml` file that declares how to deploy the pipeline containers
 
A component is organized as follows:

  - a `code` directory that contains code for the containers (that will be copied in /app)
  - a `containers` directory that contains pre-packaged containers. They can be either base images from which it is 
    possible to derive a pipeline container or fully functional containers that can be instantiated in the pipeline
  - the `docker-compose-build.yml` file that declares how to compile all images in the  

Build
------

The build of the container images is described in docker-compose-build.yml files. Each component can also provide a 
docker-compose-build.yml file for the images it defines. 


Deployment
------------

All containers are started by a docker-compose script that connect them to a private network and creates for each of 
them a volume where their data can persist. All containers of a pipeline are isolated from the rest of the system. 
Access from outside is performed via the gateway container that is mapped to a port of the host where the containers 
are running. The port where the gateway container is listening is defined in the docker-compose script. 

HTTP API endpoints
---------------------

The only endpoints accessible from outside the containers private network is the dashboard. The dashboard provides 
two entry points:
 
  - `http://localhost:XXXX/` : provides a HTML based UI to control the containers of the pipeline.
  
  - `http://localhost:XXXX/containers/YYYYY` : provides a reverse-proxy to the container YYYY.

    
The containers of the pipeline export a HTTP uniform API that allows to control them. The API has the following 
endpoints:
 
  - `/`: `GET` allows to return the description of the container (parameters required to create an artifact, 
     type of artifact generated )
     
  - `/artifacts` : `GET` returns a list of artifacts on the container, `POST` allows to create a new artifact, the 
    details 
  
  - `/artifacts/{name}/` : `DELETE` allows to remove the artifact
  
  - `/artifacts/{name}/data` : `GET` allows to download the artifact content, if the artifact is composed by multiple
    files each can be requests by appending the file name to the url. If multiple files are present and the data 
    directory is requested a zip with all the files is generated.
  
  - `/artifacts/{name}/status` : `GET` allows to retrieve the artifact status (completed/failed/in-progress)
  
  - `/artifacts/{name}/log` : `GET` allows to retrieve the logs generated during the creation of the artifact
  
  - `/artifacts/{name}/input-parameters` : `GET` allows to retrieve the parameters used during artifact creation
   
  - `/artifacts/{name}/input-files` : `GET` list the files that were submitted to create the artifact
  
  - `/artifacts/{name}/input-files/{file}` : `GET` download a file that was submitted to create the artifact
  
  - `/artifacts/{name}/metrics/{metric_name}/{view_name}` : `GET` download a metric for a specific artifact exported by 
    the container
  
  
The pipeline container exports an HTTP API that allows to get information about the pipeline and to execute it. The
 endpoints are the following:
 
  - `/task` : `GET` returns a description of the task
  
  - `/` and `/runs` : provides an artifact-like API that allows to schedule pipeline runs and retrieve 
    their the status.
    
  - `/containers` : returns a list of the containers that belong to the pipeline
  
  - `/artifacts` : returns a list of artifacts stored in the containers of the pipeline

The containers and the client tool use a python implementation of the HTTP API that is found 
in `common/bonseyes/api.py`. 
    
Containers that create artifacts 
------------------------------------

Artifact containers run uwsgi, an application server that accepts HTTP connections and executes python code for the 
dynamic content. The implementation of the APIs is done using Flask. The base implementation is found in 
`containers/common/tool_api.py`. The API is mostly independent from the artifact type being created. The only artifact 
specific function is the artifact creation. Each container provides a function that performs the creation and registers
it with the API implementation.

To perform artifact creation the container uses the mule functionality of uwsgi. This allows to queue artifact creation 
tasks from the API implementation. The mule process, a second python interpreter spawned by uwsgi, is then responsible to 
perform one after the other the creation tasks.

Each container is configured to be able to process one artifact at time. Artifact containers store their artifacts in 
the directory `/data`. Each artifact is stored in a distinct folder. Data, logs, status, input parameters, etc. are 
stored as files in the corresponding artifact folder. This is managed by code in `containers/common/local_artifact.py`. 

Containers that manages the pipeline
------------------------------------------

The container that manages the pipeline also runs uwsgi and an application in python. The base implementation is found 
in `containers/common/pipeline_api.py`. The pipeline container extends the tool API to add some methods to describe the
task carried out by the pipeline, methods to retrieve the tool containers in the pipeline (categorized in three 
classes: data and models) and methods to return all artifacts that are available in these containers.

Moreover the pipeline container uses the same mechanism of the tool containers to schedule execution of a script that
uses the HTTP APIs of the tool containers to use them in the right order to go from raw data to the model and its 
benchmarks. The actual code that is run is passed during the initialization of the api.

Dashboard container
---------------------

The dashboard container contains a uwsgi server and a python application. The application provides an api with
the following endpoints:

  - `/pipelines/` : returns the list of pipelines that are present in the project

The uwsgi server is also publishing the static files that form the dashboard web UI. The web application is 
in `containers/dashboard/bonseyes_dashboard/static` and is written in polymer. The external dependecies of the 
application are installed using bower during the dashboard docker container creation.

Visualization container
-------------------------

The visualization container is based on uwsgi and a python application. The application exposes an api that collects all
metrics from all artifacts in the pipeline and published them in tensorboad format.  

The uwsgi server publishes the python api and static files from tensorboard.

Gateway container
--------------------

The gateway container is a nginx container that works as reverse proxy to access all containers in the project. The 
reverse proxy maps all containers root directories to the url /containers/{name}/
