Formats
=======

Each format must specify two interfaces:

  - *On-disk representation*: a canonical way to store the format to disk for interchange purpose. The disk
    representation is used to guarantee consistent way to maintain at-rest data and to implement offline tools that
    generate data in the format.

  - *HTTP API*: a canonical way to access the content of a format remotely. It is used to transfer artifacts or some
    parts from a producer tool to a consumer tool and to export artifacts or parts of them from the tools.

Formats may extend other formats. A format X is said to extend a format Y another format if  the on-disk representation
of format X is a complies with the requirements of on-disk representation of format Y, and the HTTP API of format X
supports all the methods of the HTTP API of format Y.

All formats extend exactly one of the following to base formats: `com.bonseyes.format.blob` or
`com.bonseyes.format.directory`.

The `com.bonyeses.format.blob` on-disk representation is a binary blob. The HTTP API supports a single GET method at
the root that allows to download the binary blob.

The `com.bonseyes.format.directory` on-disk representation is a directory potentially containing other directories and
files. The HTTP API supports a single GET method at the root that allows to download the directory encoded as a tar
file.

Format manifests
----------------

The formats are described by files named format.yml. This file is a :doc:`YAML <yaml>` file containing the
following keys:

  - `name`: name of the format (in reverse dotted notation)

  - `title`: single line human readable name of the format

  - `description`: human readable name description of what the format is storing

  - `extends`: name of the format that the format extends

  - `on_disk_representation`: human readable description of the on-disk representation of the format

  - `http_api`: array of mappings, one for each valid endpoint of the format HTTP api with the following format

  - `endpoint`: HTTP endpoint relative to the url of the data

  - `description`: human readable description of the data returned by doing GET on the endpoint

Base formats
------------

Blob
^^^^

`com.bonseyes.format.blob`

This format represents a binary blob.

On-disk representation
""""""""""""""""""""""

The on-disk representation of this format is a single file containing the binary data.

HTTP API
""""""""

The HTTP API to access this format has the following endpoints:

  - `GET /` : returns the binary data from the on-disk representation

Directory
^^^^^^^^^

`com.bonseyes.format.directory`

This format represents a directory structure containing named binary blobs.

On-disk representation
""""""""""""""""""""""

A directory potentially containing other directories and files.

HTTP API
""""""""

The HTTP API to access this format has the following endpoints:

  - `GET /` : returns a tar containing the files and directories of the binary representation