Creating a new package
======================

Code and tools are typically developed in a package so that they can be easily be included in different workflow
projects and they can use code defined in other packages.

The structure of a package is the following:

  - `tools`: one subfolder per tool.
  - `images`: one subfolder for each base image
  - `lib`: code shared by multiple tools that share no base image

The package is typically a git repository so that workflow projects can include it as a git submodule.
