Bonseyes AI Pipeline Framework
==============================

The rapid evolution of technology in the field of machine learning requires companies to continuously update their
training pipelines. Being able to upgrade to the latest algorithm or technology is critical to maintain the leadership
in their own field.

Upgrading existing data processing pipelines is a very demanding task. Differences in library versions, runtime
environments and formats need to be handled. These challenges can consume a significant amount of time and introduce
hard to solve bugs. These problems can be partially alleviated by carefully planning how to develop the upgrade but
remain a big problem.

Moreover companies are often interested in acquiring off-the-shelf code for many parts of the pipeline: on one side to
reduce their costs and on the other to acquire advanced technology that they would not be able to develop in-house.
Integrating externally developed code is an even more challenging task as it is very likely what is acquired is not
compatible with the existing pipeline.

The main objective of the Bonseyes training pipeline framework is to alleviate this problem by defining a way to
split the training pipeline in **reusable components**, define interfaces for **interoperability** and
multi-actor development and provide a **documented reference** implementation of the interfaces to accelerate
development.

.. warning::

   This document is a draft and is subject to change without notice


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   guides/index
   reference/index
   http_apis
