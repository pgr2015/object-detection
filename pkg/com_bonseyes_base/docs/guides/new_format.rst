Developing a new data format
============================

Given the wide array of tools that can be integrated in the pipeline it is likely that at some point a tool needs to
read or output data in a format that has not been defined. To create a new data format the tool developer has two
mechanisms to define a new format:

  - *Specialize an existing format*: for instance define an HDF5 based format by specializing the
    com.bonseyes.data.database format or define a CSV based format by deriving from the com.bonseyes.format.blob format

  - *Compose existing formats*: for instance define a format that consists in two HDF5 files by composing the
    com.bonseyes.data.database format using the com.bonseyes.data.composite format

When defining a format the developer has to specify an HTTP API and a on disk format. Moreover to integrate in the
framework the format the developer has to write a format plugin. The format plugin will be used by tools that need to
produce or consume the artifact, and by the user to directly interact with the format.

Figure: Relationship between viewers, editors and server for a given format

A format plugin is composed by the following parts:

  - *Viewer*: a python object that allows to read the artifact data.
  - *Editor*: a python object that allows to edit the artifact data.
  - *Server*: a python object that provides a HTTP API to a viewer
  - *Format*: a python object that is able to construct viewers, editor and servers.

The developer has to write at least two implementation of the viewer, one for accessing the data directly from on-disk
representation and one to access the data over HTTP. For the editor is sufficient to create one implementation that is
able to modify to the on-disk representation.

In practice when specializing existing formats the developer has to implement a minimal part of the above as it can
mostly delegate the heavy lifting to the format it is specializing.

Specializing an existing format
-------------------------------

[section under construction]

The first step is to setup a project and create a package as for tool development (see the above).

Assume we want to create a new format based on HDF5 that contains a 2-D matrix that stores the distance between pairs of
points from a set. Assume we want the format to be called `$FORMAT_NAME` in the package `$PACKAGE_NAME` in the plugin
with name `$PLUGIN_NAME` and plugin python package name `$PLUGIN_PACKAGE`. The format, plugin and package name must be a
reverse dotted notation name, the plugin python package name must be a valid python package name.

The first step after the initial setup is to create the folder with the plugin::

    mkdir -p pkg/$PACKAGE_NAME/plugins/$PLUGIN_NAME/lib/$PLUGIN_PACKAGE/

Then we need to create the plugin registration script in `pkg/$PACKAGE_NAME/plugins/$PLUGIN_NAME/plugin.py`. This code
is called by the framework upon registration of the plugin and registers all formats provided by the plugin with
framework:

.. code-block:: python

    from bonseyes.api.data import data_formats


    def register():

        def create_format():
            import PLUGIN_PACKAGE.impl

            return PLUGIN_PACKAGE.impl.FACTORY

        data_formats.register(create_format, FORMAT_NAME)

Now we need to define a python api for our format, this API is used by tools code to interact with the To do so we
create the file `pkg/$PACKAGE_NAME/plugins/$PLUGIN_NAME/$PLUGIN_PACKAGE/api.py`:

.. code-block:: python

    from abc import abstractmethod, ABCMeta
    from bonseyes.api.data import DataViewer, DataEditor

    class DistanceViewer(DataViewer, metaclass=ABCMeta):

        @abstractmethod
        def get_distance(self) -> float:
            pass


    class DistanceEditor(DataEditor, metaclass=ABCMeta):

        @abstractmethod
        def initialize(self, class_count: int,
                       input_dimensions: List[Tuple[str, int]],
                       output_dimensions: List[Tuple[str, int]],
                       input_data_type: str,
                       output_data_type: str):
            pass

        @abstractmethod
        def append_sample_data(self, names: List[str],



