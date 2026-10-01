.. _autograph-corpus-build:

Building the corpus
===================

.. code-block:: python

   build = sales.autograph.corpus_build(categories=["legal", "finance"])

One call starts a corpus build for the given categories, waits until it
finishes and returns the final status. The corpus is the first layer of the
context graph: AutoGraph reads the files uploaded under each category, extracts
their text, links similar documents and groups them into clusters. The
strategizer and the import work on that result, so this is the first step of
ingestion. :ref:`autograph-ingest` runs all three steps in one call.

Before sending anything, ``corpus_build`` reloads the project and refuses if
it has no AutoGraph service.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 28 18 54

   * - Parameter
     - Type
     - Meaning
   * - ``categories``
     - sequence of ``str``
     - The categories to build. A category is the second label of the scope
       the files were uploaded with: a file uploaded with
       ``scope=["sales", "legal"]`` belongs to category ``"legal"``. At least
       one is required.
   * - ``incremental``
     - ``bool``
     - Keep the existing corpus and only add or update the given categories.
       Default ``False``, which builds the categories for the first time and
       refuses one that is already built.
   * - ``top_k``
     - ``int``, optional
     - How many similar documents are linked to each document. Service default
       7.
   * - ``cluster_threshold``
     - ``int``, optional
     - Minimum cluster size, 1 or 2. Service default 2.
   * - ``timeout``
     - ``float``, optional
     - Deadline in seconds for the whole build. Unset waits without bound.
   * - ``poll_interval``
     - ``float``
     - Seconds between two status polls. Default 30.
   * - ``on_progress``
     - callable, optional
     - Called with every polled
       :class:`~arango_ai_sdk.models.GetBuildStatusResponse`, so you can print
       or log progress. See :ref:`autograph-waiting`.

Return value
------------

The final :class:`~arango_ai_sdk.models.GetBuildStatusResponse`. Its
``status`` is ``"completed"``; a build that ends any other way raises instead.
The counts describe what the build did: ``document_count`` and
``cluster_count`` for the corpus as it is now, ``documents_added``,
``documents_removed`` and ``documents_unchanged`` for this run.

Two input files with the same name under the same category produce one corpus
document. ``documents_deduplicated`` counts how many files collapsed that way
and ``dedup_groups`` names them.

A build that completes with ``error_code`` set is a partial success: some
files could not be processed, the rest were. The call returns it and logs a
warning; it does not raise. Check ``error_code`` and ``error`` when every file
matters:

.. code-block:: python

   build = sales.autograph.corpus_build(categories=["legal"])
   if build.error_code:
       print(f"Partial build: {build.error_code}: {build.error or build.message}")

Errors
------

:exc:`ValueError`
   ``categories`` is empty. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError`
   The project has no AutoGraph service. Nothing was sent. See
   :ref:`autograph-deploy`.

:exc:`~arango_ai_sdk.exceptions.ModelConfigNotReadyError`
   AutoGraph cannot use its chat or embedding settings, either because a
   startup check found them invalid or because it is still loading them.
   Check the secret profiles and models passed to ``deploy``, or retry shortly.

:exc:`~arango_ai_sdk.exceptions.AutoGraphBusyError`
   Another build, strategizer run, orchestration or delete is in progress for
   the project. AutoGraph runs one job at a time; wait for it and retry.

:exc:`~arango_ai_sdk.exceptions.CategoryAlreadyBuiltError`
   One of the categories is already built and ``incremental`` is ``False``.
   Pass ``incremental=True`` to add to it.

:exc:`~arango_ai_sdk.exceptions.IngestionFailedError`
   The build ended as failed. ``job_status`` on the exception is the final
   :class:`~arango_ai_sdk.models.GetBuildStatusResponse`, whose ``error`` and
   ``error_code`` say why.

:exc:`~arango_ai_sdk.exceptions.JobStatusLostError`
   AutoGraph no longer has a status for the build, usually because the service
   restarted while you were waiting. The build itself may still be running.
   ``job_id`` on the exception names it.

:exc:`~arango_ai_sdk.exceptions.JobTimeoutError`
   ``timeout`` passed before the build finished. The build keeps running on the
   platform; the SDK only stopped waiting.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import CategoryAlreadyBuiltError, IngestionFailedError

   sales = client.project.get(project_name="sales")

   def show(status):
       print(f"build {status.status} {status.progress}%")

   try:
       build = sales.autograph.corpus_build(
           categories=["legal", "finance"],
           timeout=1800.0,
           on_progress=show,
       )
   except CategoryAlreadyBuiltError:
       build = sales.autograph.corpus_build(
           categories=["legal", "finance"],
           incremental=True,
       )
   except IngestionFailedError as exc:
       print(f"Build failed: {exc.job_status.error}")
   else:
       print(f"{build.document_count} documents in {build.cluster_count} clusters")
