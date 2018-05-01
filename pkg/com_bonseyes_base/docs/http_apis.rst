HTTP APIs
=========

.. contents::

Tool API
--------

    - `GET /manifest`

      Returns the manifest of the tool

    - `POST /artifacts/`

      This method supports one operation:

        - Create a new artifact

      The post body must be of type form/multipart and contain the following parts.

        - `operation`: (mime-type: `text/plain`) with value `create`
        - `artifact-name`: (mime-type: `text/plain`) with as value the name of the artifact

      Then for each parameter of the creation operation the a part must be present with the name
      `arguments.<name of the parameter>`. The mime type and encoding is described in the Value Types section.

      The successful return of this method is a application/json file with the following contents:

      .. code-block:: json

            { "command_index": "<index of the creation command>" }

      where the index of the creation command is the index used to obtain the creation command from the artifact history
      (see `GET /artifacts/<string:artifact_name>/history/`).

    - `POST /artifacts/<string:artifact_name>/`

      This method supports two operations:

        - Execute an operation on an existing artifact
        - Wait until the current operation on the artifact is completed.

      The post body must be of type form/multipart and contain the following parts.
        - `operation`: (mime-type: `text/plain`) with value `modify` or `wait_for_complete`
        - `artifact-name`: (mime-type: `text/plain`) with as value the name of the artifact

      When the operation is `modify` the parameters of the action must be sent as additional parts with name
      `arguments.<name of the parameter>` with the encoding described in `POST /artifacts`.

      The successful return of this method when the operation is `modify` is a `application/json` file with the
      following contents:

      .. code-block:: json

        { "command_index": "<index of the modification command>" }

      where the index of the creation command is the index used to obtain the creation command from the artifact history
      (see `GET /artifacts/<string:artifact_name>/history/`).

      The successful return of the method when the operation is `wait_for_complete` is a `application/json` file with
      the following contents:

      .. code-block:: json

        { "status": "<status of the artifact>" }

      Notice that the "wait_for_complete" operation may return even if the artifact didn't complete.

    - `POST /artifacts/<string:artifact_name>/history/<int:command_index>/`

      This method is used to control the execution of a given command on an artifact. It supports one operation:

        - Interrupt a command

      The post body must be of type form/multipart and contain the following parts.

        - `operation`: (mime-type: `text/plain`) with value `interrupt`

      The successful return of the method is a application/json file with the following contents:

     .. code-block:: json

      { "status": "<status of the artifact>" }

    - `DELETE /artifacts/<string:artifact_name>/`

      Deletes the artifact

    - `GET /artifacts/`

      Returns the list of artifacts created with the tool. The list of artifact is a application/JSON file containing
      an array with the names of the artifact.

    - `GET /artifacts/<string:artifact_name>/name`

      Returns the name of the artifact as plain/text.

    - `GET /artifacts/<string:artifact_name>/status`

      Returns the status of the artifact as plain/text

    - `GET /artifacts/<string:artifact_name>/history/`

      Returns the list of commands that acted on the artifact. The list of commands is a application/JSON file
      containing an object with a field "count" that contains the number of commands executed on the artifact.

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/action_name`

      Returns the name of the action that was done for the command as plain/text.

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/interrupt_requested`

      Returns the "true" is the command has been interrupted or "false" if not as plain/text.

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/log`

      Returns the log generated during the execution of the command. To retrieve incrementally the log while it is
      being generated set the header "X-Bonseyes-Follow" to true.

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/metrics/`

      Returns the list of metrics that were generated during the command execution. The list of metrics is a
      `application/json` file containing an array with the names of the metrics.

    - `GET /artifacts/<string:artifact_name>/data/<path:path>`

      Returns the data of the artifact, the exact behavior of this route depends on the data format of the tool.

    - `GET /artifacts/<string:artifact_name>/metadata/<path:path>`

      Returns the metadata of the artifact, the exact behavior of this route depends on the metadata format of the tool.

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/metrics/<string:metric_name>/<path:path>`

      Returns the metric data of the command, the exact behavior of this route depends on the metric format.

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/arguments/<string:arg_name>/`

      Returns a list of all the parameters that were passed to the action executed for the given command. The list is
      sent as an `application/json` file containing an array of names of arguments.

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/arguments/<string:arg_name>/type`

      Returns the type of value that has been sent as argument. May be `json`, `resource`, `url` or `string`.

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/arguments/<string:arg_name>/data`

      Returns the value sent as argument. The returned value depends on the type of value:

        - String value:  (mime-type: `plain/text`) UTF-8 enconded string
        - URL value: (mime-type: `plain/text`) UTF-8 enconded url
        - JSON value: (mime-type: `application/json`) serialized JSON data
        - Resource value with inline data: (mime-type: `application/binary`) binary data
        - Resource value referring to an url: (mime-type: `plain/text`) UTF-8 enconded url

    - `GET /artifacts/<string:artifact_name>/history/<int:command_index>/arguments/<string:arg_name>/subtype`

      In case the type of the value is resource this endpoint returns `inline` if the resource has inline data and `url`
      if the resource refers to a URL.

Executor API
------------

.. todo::
   To be written

Runtime API
-----------

.. todo::
   To be written

