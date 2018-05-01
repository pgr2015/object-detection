Value types
===========

Workflows and actions parameters can be one of the following: string, json, resource, archive or url. For each of these
types the framework defines a serialization that can be used to send them as parts of a HTTP `form/multipart` POST.

String values
-------------

This value represents a UTF-8 encoded string.

To send a string value in a multipart form body the part contains the string in UTF-8 encoded format while the mime
type of the part is set to the `application/vnd.com.bonseyes.data+string`.

JSON values
-----------

This value represent a JSON serializable value. This means it can contain dictionaries, lists, integer, floats,
string, etc.

To send a JSON value in a multipart form body the part contains the serialized JSON data while the mime type of the
part is set to `application/vnd.com.bonseyes.data+plainobject`.

URL values
----------

This value represents an URL.

To send the URL value in a multipart form body the part contains the UTF-8 encoded URL while the mime type is
set to `application/vnd.com.bonseyes.data+url`.

Resource values
---------------

This value represents a binary blob. The blob may optionally have a URL that allows to download it.

The serialization of a resource in a multipart body can be one of the following:

  - *Inline resource*: the binary blob of the resource is transmitted in the part body and the mime type is set
    to `application/vnd.com.bonseyes.data+resource.blob`

  - *Remote resource*: the binary blob of the resource is not transmitted directly, instead the body of the part
    contains a UTF-8 encoded url pointing to the blob. The mime-type of the part is set
    to `application/vnd.com.bonseyes.data+resource.url`.

Archive
-------

This value represents a directory structure containing some named binary blobs. The archive may optionally have a
URL that allows to download the directory structure.

The archive is downloaded from the URL as a tar file.

The serialization of an archive in a multipart body can be one of the following:

  - *Inline archive*: the archive data is transmitted in the part body as a tar file and the mime type is
    set to `application/vnd.com.bonseyes.data+archive.blob`.

  - *Remote archive*: the archive data is not transmitted directly, instead the body of the part contains a
    UTF-8 encoded url pointing to the tar encoded archive. The mime-type of the
    part is set to `application/vnd.com.bonseyes.data+archive.url`.

