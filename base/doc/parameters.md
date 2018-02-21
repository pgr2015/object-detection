Artifact Creation Parameters
===============================

The parameters of a container are described with a dictionary. Every parameter has an entry. The name of the entry
is the name of the parameter. The value of the entry is a dictionary that contains the following keys:

  - `label`: a short human readable description of the parameter

  - `type`: the type of parameter, it can be one of the following:

     - `string` : enter a string
     - `file` : upload a file
     - `artifact`: select a artifact of a given type type
     - `artifact-list`: select a list of artifacts of a given type type

  - `artifact-type`: when the type is artifact or artifact list an additional this key specifies the type of artifacts
    that can be selected (the output_type specified by the corresponding container).