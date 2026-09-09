.. _files-upload-folder:

Uploading a folder
==================

.. code-block:: python

   result = client.files.upload_folder("./corpus", scope=["acme", "legal"])

Every file under the folder, at any depth, is uploaded. Batching, partial
failures and the return value are the same as in :ref:`files-upload-many`.

Where the files land
--------------------

By default every file is stored directly under ``scope`` by its own name, no
matter how deep it sits in the folder. Two files with the same name in different
subfolders then become two versions of one file.

With ``preserve_paths=True`` each subfolder becomes one more scope label below
``scope``, so the folder structure is kept:

.. code-block:: text

   corpus/                         scope=["acme"], preserve_paths=True
   ├── overview.pdf           ->   ["acme"]                 overview.pdf
   └── legal/
       ├── nda.pdf            ->   ["acme", "legal"]        nda.pdf
       └── 2026/
           └── q1.pdf         ->   ["acme", "legal", "2026"] q1.pdf

Subfolder names then have to be valid scope labels, and the total depth may not
exceed five labels; a folder that breaks either rule is refused before anything
is sent.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 22 22 56

   * - Parameter
     - Type
     - Meaning
   * - ``folder``
     - ``str`` or ``os.PathLike``
     - The folder to walk.
   * - ``scope``
     - ``Sequence[str]``, optional
     - Ordered scope labels the folder's files are placed under. Keyword-only.
   * - ``preserve_paths``
     - ``bool``, optional
     - Turn subfolders into scope labels. Keyword-only. Defaults to ``False``.
   * - ``custom_metadata``
     - ``Mapping[str, str]``, optional
     - Metadata kept with every uploaded version. Keyword-only.
   * - ``timeout``
     - ``float``, optional
     - Seconds to wait for the platform's answer to each request. Keyword-only.
       Defaults to five minutes.

Errors
------

The same as :ref:`files-upload-many`, with three differences: a ``folder`` that
does not exist or is not a folder raises Python's :exc:`NotADirectoryError`,
:exc:`~arango_ai_sdk.exceptions.EmptyBatchError` means the folder holds no
files, and :exc:`~arango_ai_sdk.exceptions.InvalidScopeError` can also come from
a subfolder name when ``preserve_paths`` is on.
