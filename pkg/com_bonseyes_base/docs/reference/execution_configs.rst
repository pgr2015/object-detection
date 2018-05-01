Execution configuration files
=============================

The execution configuration files are used to provide environment configurations to the execution. The files are
:doc:`YAML <yaml>` files and have the following contents:

At the top level the file must contain a mapping that contains the following keys:

  - `application_config`: (optional) configuration of the application in which worker tools will be started

For the default runtime the application config is in turn an mapping with the following keys:

  - `build_args` : (optional) mapping where keys are names of buildargs passed during build of images, and values are
    their value

  - `run_opts`:  (optional) mapping with options that should be passed to the docker.run call

  - `credentials`: (optional) mapping with credentials for the remote registries that can be used to pull images. The
    keys are the name of the registry and the value is an mapping with two keys, user and password that provide the
    login credentials.

  - `default_pull_registry`: (optional) The repository from which to pull images by default. It can be set to the name
    of the registry (without trailing slash) or to a boolean. If it is set to true the images will be pulled from
    Docker Hub and if it is set to false they will not be pulled by from a repository, instead they will be
    searched locally.

  - `default_pull_tag`: (optional) the default tag to use for pulling images.
