Files
=====

You do not construct this class yourself. The client owns a
:class:`~arango_ai_sdk.files.FileManager` and exposes it as ``client.files``.
Its operations return :class:`~arango_ai_sdk.models.RagInputUploadResponse` and
:class:`~arango_ai_sdk.models.RagInputBatchItemResult` instances, documented in
:doc:`models`.

.. autoclass:: arango_ai_sdk.files.FileManager
   :members: upload_file, upload_files, upload_folder
