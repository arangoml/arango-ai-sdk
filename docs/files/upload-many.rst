.. _files-upload-many:

Uploading several files
=======================

.. code-block:: python

   result = client.files.upload_many(
       ["./q1.pdf", "./q2.pdf", "./q3.pdf"],
       scope=["acme", "reports"],
   )
   print(result.ok_count, "stored,", result.error_count, "failed")

Every file is placed directly under ``scope`` by its own name. The files are
sent in requests of at most 100 files and 2 GiB, the platform's limits per
request; you do not split them yourself.

Each file is processed independently. A file the platform rejects, for example
an empty one, is reported in the result and does not stop the others, so a
partial failure is a normal return value, not an exception. The same holds for
a request the platform fails as a whole: its files appear as failed in the
result, what earlier requests stored stays visible, and the remaining requests
still go ahead. Only errors you have to fix in the call itself are raised.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 22 22 56

   * - Parameter
     - Type
     - Meaning
   * - ``paths``
     - ``Iterable[str or os.PathLike]``
     - The files to upload.
   * - ``scope``
     - ``Sequence[str]``, optional
     - Ordered scope labels every file is placed under. Keyword-only.
   * - ``custom_metadata``
     - ``Mapping[str, str]``, optional
     - Metadata kept with every uploaded version. Keyword-only.
   * - ``timeout``
     - ``float``, optional
     - Seconds to wait for the platform's answer to each request. Keyword-only.
       Defaults to five minutes.

Return value
------------

A :class:`~arango_ai_sdk.models.BatchUploadResult` with one
:class:`~arango_ai_sdk.models.BatchItemResult` per file, in the order given.
Check :attr:`~arango_ai_sdk.models.BatchItemResult.ok` before reading an item's
storage attributes, which are ``None`` for a failed file;
:attr:`~arango_ai_sdk.models.BatchItemResult.detail` says why it failed.

.. code-block:: python

   for item in result.failed:
       print(f"{item.name}: {item.detail}")

Errors
------

:exc:`FileNotFoundError`, :exc:`IsADirectoryError`
   A path does not exist, or is a folder. Raised before anything is sent.

:exc:`~arango_ai_sdk.exceptions.InvalidScopeError`
   The scope breaks the platform's rules. Normally raised before anything is
   sent.

:exc:`~arango_ai_sdk.exceptions.EmptyBatchError`
   ``paths`` is empty. Raised before anything is sent.

:exc:`~arango_ai_sdk.exceptions.BatchTooLargeError`
   One file alone is larger than a request may carry. Raised before anything is
   sent; upload that file with :ref:`files-upload`, which has no size limit.

:exc:`~arango_ai_sdk.exceptions.InvalidFileMetadataError`
   The platform rejected ``custom_metadata``.

Failures of the connection or of authentication surface as the general SDK
exceptions described in :ref:`errors`.
