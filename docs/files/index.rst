.. _files:

Files
=====

Files are the documents the ingestion will read. You upload them once, under a
*scope*, and the ingestion finds them there. A scope is an ordered list of up to
five labels and works like a folder path: ``["acme", "legal"]`` places a file in
the ``legal`` part of the ``acme`` project. A file is identified by its database,
its scope and its name together, so uploading the same name under the same scope
again stores a new version of that file, never a duplicate.

The files area is the ``files`` namespace on the client:

.. code-block:: python

   uploaded = client.files.upload("./contracts/nda.pdf", scope=["acme", "legal"])
   print(uploaded.id, uploaded.version)

.. toctree::
   :maxdepth: 1

   upload
   upload-many
   upload-folder

Available operations
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Operation
     - Status
     - Page
   * - Upload one file
     - Available
     - :ref:`files-upload`
   * - Upload several files
     - Available
     - :ref:`files-upload-many`
   * - Upload a folder
     - Available
     - :ref:`files-upload-folder`
   * - List, download or delete files
     - Not yet available
     - Arrives in a later release.

Scopes
------

Every upload takes a ``scope``. The platform accepts at most five labels, each
1 to 128 characters of letters, digits, underscores and hyphens, and at most
256 characters combined. The SDK checks these rules before sending anything, so
a bad scope fails immediately rather than after the transfer, with an
:exc:`~arango_ai_sdk.exceptions.InvalidScopeError`.

Labels are part of how the platform stores a file, so shorter labels leave more
room for long file names. Reordering the labels addresses a different file.

Versions and deletion
---------------------

Uploading a file whose name and scope already exist stores version 2, 3 and so
on of the same file; the returned :attr:`~arango_ai_sdk.models.UploadedFile.id`
stays the same and ``version`` increases. Re-running an upload is therefore safe.

A new upload is marked ``safe_to_delete``. Once the ingestion has built a graph
from a file it locks it, so a file in use cannot be removed by accident.

Waiting for the platform
------------------------

The platform stores the files of a request one after another and answers when
the last one is written, so a large upload can take minutes to return. Uploads
therefore wait up to five minutes for the answer instead of the connection's
usual timeout. Pass ``timeout`` (in seconds) to any upload method for a very
large file or a slow deployment. The platform's own gateway stops waiting after
fifteen minutes and answers with an error of its own, so values above that
have no effect.
