.. highlight:: shell

Executing existing workflows
============================

Running a workflow
------------------

To run a workflow use the following command::

    be-admin run path/to/my/workflow.yml
    
This command will create a new execution with a random name. 
If you want to specify the name you can add the `--name` parameter::

    be-admin run path/to/my/workflow.yml --name my_execution
    
This will create a new execution name `my_execution`, if the execution 
already exists the command will return an error.

To force to overwrite the existing execution you can add the `--force`
parameter::

    be-admin run path/to/my/workflow.yml --name my_execution --force
   
If the workflow requires parameters you can pass them with the following
 parameters:

  - `--param NAME string SOME_STRING`: pass `SOME_STRING` as string to the 
    parameter `NAME` of the workflow
    
  - `--param NAME url SOME_URL`: pass `SOME_URL` as url to the parameter 
    `NAME` of the workflow
    
  - `--param NAME file PATH`: pass the contents of file `PATH` as resource
    to the parameter `NAME` of the workflow
   
  - `--param NAME json PATH`: pass the parsed contents of the json file 
    at position `PATH` to the parameter `NAME` of the workflow
    
  - `--param NAME yaml PATH`: pass the parsed contents of the YAML file 
    at position `PATH` to the parameter `NAME` of the workflow
    
  - `--param NAME execution-output EXECUTOR EXECUTION OUTPUT`: add the 
    worker providing the output `OUTPUT` of the execution `EXECUTION` 
    on executor `EXECUTOR` as a source to the workflow and pass the 
    output as url to the parameter `NAME` of the workflow. The executor 
    parameter is a url to the executor, to use the local executor set 
    it to `local:`.
  
  - `--param NAME execution-worker EXECUTOR EXECUTION WORKER`: add the 
    worker `WORKER` from execution `EXECUTION` on executor `EXECUTOR`
    as a source to the workflow and pass its url as url to the parameter 
    `NAME` of the workflow. The executor parameter is a url to the 
    executor, to use the local executor set it to `local:`.
    
  - `--param NAME execution-artifact EXECUTOR EXECUTION WORKER ARTIFACT`:
    add the worker `WORKER` from execution `EXECUTION` on executor
    `EXECUTOR` as a source to the workflow and pass its artifact named
    `ARTIFACT` as url to the parameter `NAME` of the workflow. The
    executor parameter is a url to the executor, to use the local
    executor set it to `local:`.
   
For example to pass the file `test.txt` as parameter `param1` and 
the string `test` as parameter `param2` to the workflow `sample.yml`
then the command would be::

    be-admin run sample.yml --param param1 file test.txt \
                            --param param2 string test
                            
                            
How to save artifacts locally
-----------------------------

To collect artifacts produced by a workflow during its execution you can add the `--save` parameter to the `run`
command. There are multiple options depending on which artifact you want to collect.

    - `--save output $OUTPUT_NAME $OUTPUT_FILE` to collect the output `$OUTPUT_NAME` to `$OUTPUT_FILE`

    - `--save step $STEP_NAME $OUTPUT_FILE` to collect the artifact produced at step `$STEP_NAME` to `$OUTPUT_FILE`

    - `--save worker $WORKER_NAME $ARTIFACT_NAME $OUTPUT_FILE` to collect the artifact `$ARTIFACT_NAME` on the worker
      `$WORKER_NAME` and save it to `$OUTPUT_FILE`

You can also collect the results of a previous execution by using the `save` command as follows::

    be-admin save $EXECUTION_NAME output $OUTPUT_NAME $OUTPUT_FILE
    be-admin save $EXECUTION_NAME step $STEP_NAME $OUTPUT_FILE
    be-admin save $EXECUTION_NAME worker $WORKER_NAME $ARTIFACT_NAME $OUTPUT_FILE

The different commands work like the `--save` options described above.


How to clean up previous executions
-----------------------------------

To remove all tool instances (and their volumes) and artifacts of a previous execution you can remove it with
the following command::

    be-admin rm $EXECUTION_NAME

This command will remove everything that was generated during the execution, with the following exceptions:

  - Docker images are not removed (to allow caching of the image). To remove them you can delete all unused images
    with docker commands.

  - If an artifact or worker as been used as a source in other workflows the corresponding volume is not deleted. It
    will be deleted automatically when all executions referencing the artifact or worker will be deleted.


Create a custom execution configuration
---------------------------------------

It is possible to configure various environment parameters for an 
execution by creating a YAML configuration file. The configuration can 
be passed to the be-admin run command with the parameter `--config`.

For the syntax of these files check the corresponding section in the 
reference chapter of this guide.

