.. _files:

Files
=====

Files are the documents the ingestion will read. You upload them once, under a
*scope*, and the ingestion finds them there. A scope is an ordered list of up to
five labels and works like a folder path: ``["acme", "legal"]`` places a file in
the ``legal`` part of ``acme``. A file is identified by its database, its scope
and its name together, so uploading the same name under the same scope again
stores a new version of that file, never a duplicate.

The files area is the ``files`` namespace on the client:

.. code-block:: python

   uploaded = client.files.upload("./contracts/nda.pdf", scope=["acme", "legal"])
   print(uploaded.id, uploaded.version)

Available operations
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Operation
     - Status
     - Section
   * - Upload one file
     - Available
     - :ref:`files-upload`
   * - Upload several files
     - Available
     - :ref:`files-upload-files`
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

.. _files-upload:

Uploading one file
------------------

.. code-block:: python

   uploaded = client.files.upload(
       "./contracts/nda.pdf",
       scope=["acme", "legal"],
       name="nda-2026.pdf",                 # optional, defaults to the file's name
       custom_metadata={"owner": "legal"},  # optional
   )

The file is streamed from disk, never read into memory as a whole. The call
returns an :class:`~arango_ai_sdk.models.UploadedFile` describing the stored
version.

``custom_metadata`` is a flat string-to-string mapping kept with this version
and returned on later reads. Each version carries its own; the next upload
replaces it rather than merging.

Errors: a path that does not exist or is a folder raises Python's
:exc:`FileNotFoundError` or :exc:`IsADirectoryError`; an empty file raises
:exc:`~arango_ai_sdk.exceptions.EmptyFileError`; a bad scope raises
:exc:`~arango_ai_sdk.exceptions.InvalidScopeError`. All three happen before
anything is sent. Rejected metadata raises
:exc:`~arango_ai_sdk.exceptions.InvalidFileMetadataError`, and a platform that
could not store the file raises
:exc:`~arango_ai_sdk.exceptions.FileUploadFailedError` after rolling the upload
back.

.. _files-upload-files:

Uploading several files
-----------------------

.. code-block:: python

   # All under one scope
   results = client.files.upload_files(
       ["./contracts/nda.pdf", "./contracts/msa.pdf"],
       scope=["acme", "legal"],
   )

   # Each under its own scope
   results = client.files.upload_files({
       "./contracts/nda.pdf": ["acme", "legal"],
       "./reports/q1.pdf": ["acme", "finance", "2026"],
   })

The files go to the platform in one request and are stored one by one, each
under its own file name. A file the platform rejects, for example an empty one,
is reported in the result and does not stop the others.

One request carries at most 100 files and 2 GiB in total. A larger set is
refused before anything is sent with
:exc:`~arango_ai_sdk.exceptions.BatchTooLargeError`; split it across several
calls. To store a file under a different name, use :ref:`files-upload` with
``name``.

The return value
~~~~~~~~~~~~~~~~

A list with one :class:`~arango_ai_sdk.models.FileUploadResult` per file, in
the order given. Each result wraps the stored file rather than being one,
because a file can be rejected while the others are stored: when
:attr:`~arango_ai_sdk.models.FileUploadResult.ok` is true, ``result.file`` is
the same :class:`~arango_ai_sdk.models.UploadedFile` a single upload returns;
otherwise it is ``None`` and ``result.detail`` says why.

.. code-block:: python

   for result in results:
       if result.ok:
           print(result.file.id, result.file.version)
       else:
           print(result.name, result.detail)

Two files with the same name under the same scope in one call are stored as
version 1 and version 2 of that file, in order.

Errors: ``ValueError`` for an empty list, or for giving a scope both for all
files and per file; :exc:`FileNotFoundError` or :exc:`IsADirectoryError` for a
bad path; :exc:`~arango_ai_sdk.exceptions.InvalidScopeError` and
:exc:`~arango_ai_sdk.exceptions.BatchTooLargeError` as above. All before
anything is sent. :exc:`~arango_ai_sdk.exceptions.InvalidFileMetadataError`
comes from the platform.

.. _files-upload-folder:

Uploading a folder
------------------

.. code-block:: python

   results = client.files.upload_folder("./contracts", scope=["acme", "legal"])

Uploads the files directly inside the folder, all under ``scope`` and each by
its own name, in alphabetical order. **Subfolders are ignored**, together with
everything in them: to upload a nested layout, call ``upload_folder`` once per
folder, or :ref:`files-upload-files` with a mapping.

Everything else, limits, return value and errors, is as in
:ref:`files-upload-files`. In addition, a ``folder`` that does not exist or is
not a folder raises Python's :exc:`NotADirectoryError`, and a folder with no
files raises ``ValueError``.

Waiting for the platform
------------------------

The platform stores the files of a request one after another and answers when
the last one is written, so a large upload can take minutes to return. Uploads
therefore wait up to five minutes for the answer instead of the connection's
usual timeout. Pass ``timeout`` (in seconds) to any upload method for a very
large file or a slow deployment. The platform's own gateway stops waiting after
fifteen minutes and answers with an error of its own, so values above that
have no effect.
