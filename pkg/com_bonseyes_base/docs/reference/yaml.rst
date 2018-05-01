Introduction to YAML
====================

YAML_ (YAML Ain't Markup Language) is a text-based human readable language to serialize data. It is a strict superset
of JSON and therefore any JSON document is a valid YAML file.

In this chapter we show the basic features of YAML not present in JSON that are particularly useful for use with
the framework.
.

.. _YAML: https://en.wikipedia.org/wiki/YAML


.. warning::

   Make sure you don't use TABs in your YAML documents or you will run into problems.


Datatypes
-------------------

YAML supports the following data types:

  - Scalars (e.g. strings, numbers, ...)
  - Sequences (a.k.a. arrays)
  - Mappings (a.k.a. dictionaries)

Scalar
------

Scalars can be represented as in JSON, i.e. quoted string and number or boolean literals, ...

Strings can be represented like in JSON as quoted string (`"string1"`) but when there is no ambiguity the strings
can also be not quoted (`string1`), or quoted with apostrophes (`'string1'`).

Sequences
---------

Sequences can be either be encoded like in JSON using the `[item1, item2]` syntax or as follows:

.. code-block:: yaml

   - item1
   - item2

Mappings
--------

Mappings can be either encoded like in JSON using the `{ "key1": "value1", "key2": "value2"}` syntax or as follows:


.. code-block:: YAML

   key1: value1
   key2: value2


Comments
--------

YAML supports comments. The beginning of a comment is represented by the `#` symbol:

.. code-block:: yaml

   somevalue   # this is a comment

