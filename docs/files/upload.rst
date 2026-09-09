.. _files-upload:

Uploading one file
==================

.. code-block:: python

   uploaded = client.files.upload(
       "./contracts/nda.pdf",
       scope=["acme", "legal"],
       custom_metadata={"citable_url": "https://docs.example.com/legal/nda"},
   )

The file is streamed from disk, so its size is not limited by memory.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 22 22 56

   * - Parameter
     - Type
     - Meaning
   * - ``path``
     - ``str`` or ``os.PathLike``
     - The file to upload.
   * - ``scope``
     - ``Sequence[str]``, optional
     - Ordered scope labels, see :ref:`files`. Keyword-only. Empty places the
       file at the database root.
   * - ``name``
     - ``str``, optional
     - Name the file is stored under. Keyword-only. Defaults to the file's own
       name.
   * - ``custom_metadata``
     - ``Mapping[str, str]``, optional
     - Flat string-to-string metadata kept with this version and returned on
       later reads, for example a URL to cite. Keyword-only. Replaced, not
       merged, by the next version. At most 32 keys; keys up to 64 characters,
       values up to 2048, 16 KiB in total.
   * - ``timeout``
     - ``float``, optional
     - Seconds to wait for the platform's answer. Keyword-only. Defaults to
       five minutes.

Return value
------------

An :class:`~arango_ai_sdk.models.UploadedFile` describing the stored version:
its ``id``, ``version``, detected ``content_type``, ``size`` and the rest.

Errors
------

:exc:`FileNotFoundError`, :exc:`IsADirectoryError`
   ``path`` does not exist, or is a folder. Python's standard exceptions, since
   the problem is on your disk, not on the platform.

:exc:`~arango_ai_sdk.exceptions.InvalidScopeError`
   The scope breaks the platform's rules. Normally raised before anything is
   sent, since the SDK applies the platform's rules first.

:exc:`~arango_ai_sdk.exceptions.EmptyFileError`
   The file has no content. Normally raised before anything is sent.

:exc:`~arango_ai_sdk.exceptions.InvalidFileMetadataError`
   The platform rejected ``custom_metadata``.

:exc:`~arango_ai_sdk.exceptions.FileUploadFailedError`
   The platform could not store the file and reports having rolled the upload
   back, so nothing is left behind.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import InvalidScopeError

   try:
       uploaded = client.files.upload("report.pdf", scope=["acme", "Q1 2026"])
   except InvalidScopeError as exc:
       print(f"Fix the scope: {exc}")   # spaces are not allowed in a label
   else:
       print(f"Stored {uploaded.name} as version {uploaded.version}")
