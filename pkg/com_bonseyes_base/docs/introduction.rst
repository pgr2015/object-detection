Introduction
============

.. contents::

Motivation
----------

The rapid evolution of technology in the field of machine learning requires companies to continuously update their
training pipelines. Being able to upgrade to the latest algorithm or technology is critical to maintain the leadership
in their own field.

Upgrading existing data processing pipelines is a very demanding task. Differences in library versions, runtime
environments and formats need to be handled. These challenges can consume a significant amount of time and introduce
hard to solve bugs. These problems can be partially alleviated by carefully planning how to develop the upgrade but
remain a big problem.

Moreover companies are often interested in acquiring off-the-shelf code for many parts of the pipeline: on one side
to reduce their costs and on the other to acquire advanced technology that they would not be able to develop in-house.
Integrating externally developed code is an even more challenging task as it is very likely what is acquired is not
compatible with the existing pipeline.

The main objective of the Bonseyes training pipeline framework is to alleviate this problem by defining a way to split
the training pipeline in reusable components, define interfaces for interoperability and multi-actor development and
provide a documented reference implementation of the interfaces to accelerate development.

Main concepts
-------------

The main ideas of the pipeline are two, on one side isolate the different parts of the pipeline along with their
dependencies and on the other part insert in the glue code that combines them explicit and when possible standardized
interfaces that enable to easily substitute a part with a different implementation.

.. _concepts:

.. digraph:: G
    :align: center
    :caption: Figure: The three main concepts of the pipeline framework

    rankdir = LR
    node [ shape = "box" ]
    "Workflow" -> "Tool" [ label = "controls" ]
    "Tool" -> "Artifact" [ label = "creates/modifies" ]


The framework is structured around three concepts (see :ref:`figure above <concepts>`):

  - *Tool*: a software component that performs a specific function in the pipeline.

  - *Artifact*: the product of the execution of a tool. It can be an output of the pipeline or an intermediate result
    that is processed by other tools.

  - *Workflow*: a declarative pipeline description that lists the tools that need to be used and the artifacts that need
    to be created.

.. _framework:

.. digraph:: G
    :align: center
    :caption: Relationship between workflows, executor, runtime environment, tools and artifacts

    compound=true

    rankdir = LR

    node [ shape = "box" ]

    "Workflow" -> "Executor"

    subgraph cluster_runtime {

        label = "Runtime Environment"

        subgraph cluster_tool {

            label = "Tool Instance"

            "Artifact"
        }

    }

    "Executor" -> "Artifact" [ lhead=cluster_tool ]

The framework allows the user to define through formats plugins three aspects of the contents of artifacts
(see :ref:`figure above <framework>`):

  - *Data*: the actual data of an artifact (for instance a dataset)

  - *Metadata*: metadata about artifacts contents (for instance statistics about a dataset)

  - *Metrics*: structured information about the execution of the tool (for instance the progress of the
    transformation of a dataset)

The pipeline provides a collection of standard formats that define on-disk serialization and HTTP REST API for them.
The user is able to define additional formats with different interfaces.


Figure 2: Relationship between workflows, executor, runtime environment, tools and artifacts

To enable the execution of tools and workflows the following additional components are defined by the
framework (see Figure 2):

  - *Runtime Environment*: a software component that is capable of instantiating and executing the tools

  - *Executor*: a software component that is capable of executing a workflow

The framework defines the following HTTP API:

  - *Tool API*: provides a way to create artifacts, modify them and provide a reference to their data, metadata and
    metrics

  - *Runtime Environment API*: provides a way to build, instantiate and destroy tools

  - *Executor API*: provides a way to schedule and monitor the execution of a workflow

  - *Artifact API*: provides a way to remotely access an artifact

The APIs are based on HTTP to achieve network transparency and to be easy to consume and implement. Note that the Tool
API is designed in such way that it can return references to the data. This makes sure that the actual data doesn't need
to be transferred via HTTP when a better transfer method is available.

In addition to HTTP APIs the framework defines a file format for artifacts. This allows to generate, store and process
offline the artifacts. This is particularly useful, on one side to crete warehouses with artifacts, and on the other
side to generate by just reading and writing files on disk.

To enable code reuse across different workflows and tools the pipeline uses a very simple package format. Tools,
workflow and supporting code can be grouped in packages that can be included in multiple projects.

Tools
^^^^^

The pipeline framework allows to use existing tools and develop new ones. A tool needs to be first instantiated from an
image to be used . The developer specifies how the image can be obtained (built from sources or downloaded from a
registry) and the user instantiates the tool using the image. The tool can then be used to create and modify artifacts.

A tool is described with a manifests. This manifest is written by the tool developer and used by the workflow developer.
It is a YAML file that contains: a textual description of the tool, information used by the runtime environment to
instantiate the tool (how to obtain the image), a reference to the format of artifact produced by the tool (data and
metadata) and a specification of the actions the tool supports along with their parameters and metrics.

In order to reuse common dependencies shared by multiple tools the framework allows to create base images. A base image
for multiple tools can be defined using a simplified manifest that define no actions. The individual tools can then
declare that their image is built on top of this base.

The framework provides a reference implementation for the tools based on Docker. Each tool corresponds to a Docker
image and a tool instance is a Docker container. The Docker technology has been chosen because it can wrap any Linux
executable, it is lightweight, it is in widespread use and works well with GPUs. In this implementation the runtime
environment is a wrapper of the Docker engine.

The Tool API is provided by an HTTP agent installed in the container. The HTTP agent invokes Python3 code written by
the tool developer that then calls the actual implementation of the tool. For instance the Python 3 code can invoke
a Linux binary with some command line parameters and capture its output to be stored as artifact data. The HTTP agent
in the container also provides access to the artifacts  and thanks to format plugins to their data, the parameters
used to create and modify them and their metadata. By default these are stored as files in Docker volumes attached
to the tool instance.

Artifacts
^^^^^^^^^

Artifacts are accessible through the tool that created them. All artifacts share some common metadata such as the
history of operation that were carried out on them, their state and logs.

In addition to common information the artifacts, depending on their type provide access to format specific data,
metadata and metrics. The pipeline framework specifies a set of standard data formats, on-disk representations and
HTTP APIs to access them over the network.

The pipeline provides some generic formats and some additional  specialized formats that cover the typical artifacts
in a training pipeline:

  - Datasets, their metadata and metrics for tools that work on them
  - Models
  - Inference results
  - Measurement reports

The framework provides a way to add new formats, to compose existing formats and specialize them.

Workflows
^^^^^^^^^

In order to coordinate the operation of multiple tools the framework provides a workflow language that allows the tool
user to define a set of tools to be instantiated and a set of operations to carry out with them.

Workflow are described in YAML file that define which tools need to be instantiated and which artifacts needs to be
created (along with the parameters for their creation). A workflow can also have parameters.

The user can execute workflows using an executor. The executor uses the runtime environment to first instantiate the
tools and then controls them to create the artifacts. The pipeline provides both a executor that runs on a local machine
as well as a executor server that can be controlled remotely.
