Workflow definitions
====================

.. contents::

Overview
--------

A workflow definition file is a :doc:`YAML <yaml>` file that describes how to use a set of tools to produce a set of
artifacts. The workflow definition file contains a mapping described in the next section.

Workflow
--------

The workflow is a mapping containing the following keys:

  - `description`: (required) a human readable description of the workflow

  - `parameters`: (optional) a mapping containing the parameters that the workflow accepts

  - `outputs`: (optional) a mapping containing the outputs that the workflow will produce

  - `workers`: (required) a mapping containing the tools that need to be instantiated to perform the workflow

  - `steps`: (required) a sequence of steps that need to be carried out to perform the workflow

Parameters
----------

The parameters section of the workflow is a mapping, the key of the mapping is the name of the parameter and the value
is a description of the parameter. The parameters mapping is the same as the one described in the actions section of the manifest.

Outputs
-------

The outputs section of the workflow lists all the outputs of the workflows. The workflow outputs either artifacts or
urls pointing to a tool. The value of an output is assigned during the workflow execution by a workflow step. This
section is a mapping: the key is the name of the output and the values are a description properties of the output.

The description of the output is a mapping containing the following keys:

  - `label`: (optional) a human readable description of the label

Example:

.. code-block:: yaml

    outputs:
      output1:
        label: "Output 1"
      output2:
        label: "Output 2"


Workers
-------

The workers section of the workflow lists all the tools that need to be instantiated to perform the workflow. The
workers section is a mapping where the name of the worker is the key and its description is the value.

The description of the worker is a mapping containing the following keys:

  - `manifest`: (required) path starting with "./" and relative to the context in which the workflow is executing
    pointing to a tool manifest. The tool manifest contains the instruction on how to instantiate the tool.

  - `environment`: (optional) mapping containing the environment variables that are passed to the worker when it
    starts. The key is the name of the variable and the value is the value of the variable.

Example:


.. code-block:: yaml

    workers:
      worker1:   # this is the name of the worker
        manifest: ./tool/test/manifest.yml    # this is the tool manifest
        environment:
          VARIABLE1: some_value   # this is a environment variable passed to the tool

Steps
-----

The steps section of the workflow lists the sequence of steps that need to be performed by the executor during the
workflow. Each entry in the list is a step description.

For example:

.. code-block:: yaml

    steps:

        - < description of first step >
        - < description of second step >

There are two types of steps:

 - steps where the executor instructs a worker to create an artifact
 - steps where the executor suspends the workflow to let the user to interact with tools

Each step description is a mapping that contains the following keys:

  - `description`: (required) human readable description of the step

  - `name`: (optional) name of the step

  - `outputs`: (optional) mapping of output assignments done by the step (see `Output assignments`_)

If in the step the executor must request generation of an artifact then the following additional keys are present:

  - `worker`: (required) name of the worker (specified in the workers section) that must generate the artifact

  - `artifact_name`: (optional) name of artifact that will be generated, if the artifact name is not specified then the
    name of the step is used as artifact name. If the name is not present and the step has no name then an error is
    generated.

  - `parameters`: (optional) mapping containing the arguments that need to be passed to the tool to generate the
    artifact. The key is the name of the parameter, the value is an expression (see the `Expressions`_). The parameters
    in specified in this section are the parameters that are listed in the tool manifest and must match.

  - `output`: (optional) name of the workflow output to which the generated artifact should be assigned

Example:

.. code-block:: yaml

    - description: "Create an artifact"
      worker: worker1
      parameters:
        param1: "somevalue"

If in the step the executor must suspend the execution then the following additional keys are present:

  - `wait`: empty value used to indicate that the step should suspend the execution

Example:

.. code-block:: yaml

    - description: "Suspend execution"
      wait:

Output assignments
^^^^^^^^^^^^^^^^^^

Output assignments are used to map artifact or workers URL to workflow outputs. When the workflow starts nothing is
assigned to all workflow outputs. At each step the executor can be instructed to assign an artifact or a worker URL to
one of the outputs. To do so the output assignment section is used.

When a step has an output assignments section the executor will assign the specified value to each of the outputs
specified in each output assignment. When a client queries the executor it can then obtain this information. For
instance be-admin queries the executor when the execution is suspended to display the url of all outputs that have been
assigned up to that point and displays them to the user.

Output assignments are always mappings the allowed keys depend on the assignment type.

Artifact output assignments
"""""""""""""""""""""""""""

When the assignment assigns an artifact to an output then the following keys are available:

  - `worker`: the name of the worker that hosts the artifact to assign to the output

  - `artifact`: the name of the artifact to assign to the output

When the assignment assigns the artifact produced by a step to the output then the following keys are available:

  - `step`: the name of the step whose output should be assigned to the output

Both options are used when the output of the workflow should be an artifact. For example:

.. code-block:: yaml

    workers:
        importer:
            manifest: path/to/manifest.yml

    outputs:
        imported_data:
            label: "Imported data"

    steps:

        - description: "Import data"
          name: import_data
          worker: importer

        - description: "Wait for user to download data"
          wait:
          outputs:
            imported_data:
                step: import_data

or the equivalent:

.. code-block:: yaml

    workers:
        importer:
            manifest: path/to/manifest.yml

    outputs:
        imported_data:
            label: "Imported data"

    steps:

        - description: "Import data"
          worker: importer
          artifact_name: data

        - description: "Wait for user to download data"
          wait:
          outputs:
            imported_data:
                worker: importer
                artifact: data


To assign artifacts to outputs however is usually less verbose and more clear to use the `output` key:

.. code-block:: yaml

    workers:
        importer:
            manifest: path/to/manifest.yml

    outputs:
        imported_data:
            label: "Imported data"

    steps:

        - description: "Import data"
          name: import_data
          worker: importer
          output: imported_data

        - description: "Wait for user to download data"
          wait:

Worker output assignments
"""""""""""""""""""""""""

When the assignment assigns a worker to an output then the following keys are available:

  - `worker`: the name of the worker to assign to the output

This type of assignment is typically used when the workflow contains an interactive tool to prompt the user with the url
to the tool:

.. code-block:: yaml

    workers:
        annotator:
            manifest: path/to/manifest.yml

    outputs:
        annotator_url:
            label: "Annotator tool GUI URL"

    steps:

        - description: "Create a new annotation session"
          name: create_session
          worker: annotator

        - description: "Suspend execution to let user interact with the annotator tool"
          wait:
          outputs:
            annotator_url:
                worker: annotator

In this example the executor creates an annotator tool, starts an annotation session and yields the url of the annotator
to the user so that it can browse to it.

Expressions
^^^^^^^^^^^

Expressions are used in step definitions to declare the values that should be sent to the tools when creating
artifact. Each expression evaluates to a value that can be passed as parameter.

Expression can be one of the following:

  - *Literal string*: A string, in this case it evaluates to a string value

  - *Sequence*: A sequence, in this case it evaluates to a json array. To compute each entry of the array the value is
    treated as an expression and evaluated independently.

  - *Macro*: A mapping containing a type key, it is evaluated with the rules below. The additional keys in the mapping
    are passed as arguments to the macro

  - *Mapping*: A mapping not containing a type key. It is evaluated to a json object. To compute the value of each
    entry of the object, each entry in the mapping is evaluated as an expression.

The following macros are supported:

  - `workflow-parameter (name)`: returns the value passed as workflow. This macro requires an additional key name
    that specifies the name of the parameter

  - `artifact (step_name)`: returns the artifact produced by the step with name step_name as a resource

  - `artifact (worker, name)`: returns the artifact with name name from worker worker as a resource

  - `workflow-context-file(name)`: returns the file with name name from the execution context as a resource

  - `environment(name)`: returns the value in the environment of the execution with name name as a string

  - `worker-url(name)`: returns the url of the worker with name name as a url
