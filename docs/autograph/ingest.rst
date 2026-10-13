.. _autograph-ingest:

Ingesting in one call
=====================

.. code-block:: python

   result = sales.autograph.ingest(categories=["legal", "finance"])

One call runs the whole ingestion for the given categories and returns the
outcome of every step: it builds the corpus, runs the strategizer, reads the
stored strategies and imports the graph. Each step waits for the previous one
to finish. There is no single platform endpoint for this; the SDK sequences
the four calls for you.

``ingest`` is the call to make when you want the context graph and do not
need to intervene between the steps. Call the steps yourself, see
:ref:`autograph-corpus-build`, :ref:`autograph-strategize`,
:ref:`autograph-strategies` and :ref:`autograph-orchestrate`, when you want
to inspect the corpus before choosing strategies, pass build or strategizer
options ``ingest`` does not expose, or redo one step only.

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
     - The categories to ingest. A category is the second label of the scope
       the files were uploaded with. At least one is required. Passed to the
       corpus build, the strategizer and the import. ``strategies()`` takes
       no categories and returns every stored strategy for the project.
   * - ``complexity``
     - :class:`~arango_ai_sdk.models.RagStrategizerComplexity`
     - Passed to the strategizer: what share of the clusters gets a full
       knowledge graph. Default ``high``. See :ref:`autograph-strategize`.
   * - ``incremental``
     - ``bool``
     - Passed to the corpus build only. Default ``False``, which builds the
       categories for the first time and raises
       :exc:`~arango_ai_sdk.exceptions.CategoryAlreadyBuiltError` for one
       that is already built. Pass ``True`` to ingest again after adding
       files.
   * - ``timeout``
     - ``float``, optional
     - One deadline in seconds for the whole run, shared by the steps: what
       the build uses is gone for the strategizer and the import. Unset waits
       without bound.
   * - ``poll_interval``
     - ``float``
     - Seconds between two status polls, passed to each step. Default 30.
   * - ``on_progress``
     - callable, optional
     - Called with an :class:`~arango_ai_sdk.managers.autograph.IngestProgress` for
       every poll of every step. See :ref:`autograph-waiting`.

Return value
------------

An :class:`~arango_ai_sdk.managers.autograph.IngestResult` with four attributes, one
per step:

``build``
   The final :class:`~arango_ai_sdk.models.GetBuildStatusResponse`. A partial
   build, one that completed with ``error_code`` set, lands here too; it does
   not stop the run.

``strategize``
   The final :class:`~arango_ai_sdk.models.GetRagStrategizerJobStatusResponse`,
   progress counts only.

``strategies``
   The :class:`~arango_ai_sdk.models.GetRagStrategizerStrategyResponse` read
   after the strategizer finished: which cluster got which strategy.

``orchestration``
   The final :class:`~arango_ai_sdk.models.GetOrchestrationStatusResponse`,
   or ``None`` when every category was already up to date and the import had
   nothing to do.

Progress
--------

``on_progress`` receives one :class:`~arango_ai_sdk.managers.autograph.IngestProgress`
per poll. Its ``step`` is ``"build"``, ``"strategize"`` or ``"orchestrate"``
and its ``status`` is the status object that step just polled, so the fields
on it differ per step:

.. code-block:: python

   def show(progress):
       if progress.step == "build":
           print(f"build {progress.status.progress}%")
       elif progress.step == "strategize":
           print(f"strategize {progress.status.clusters_done}/{progress.status.clusters_total}")
       else:
           print(f"orchestrate {progress.status.phase}")

   result = sales.autograph.ingest(categories=["legal"], on_progress=show)

Errors
------

``ingest`` stops at the first step that fails and raises whatever that step
raised, so every error listed on the three step pages can come out of it.
The ones you are most likely to handle:

:exc:`ValueError`
   ``categories`` is empty. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError`
   The project has no AutoGraph service. Nothing was sent. See
   :ref:`autograph-deploy`.

:exc:`~arango_ai_sdk.exceptions.CategoryAlreadyBuiltError`
   A category is already built and ``incremental`` is ``False``. Nothing after
   the build request was sent.

:exc:`~arango_ai_sdk.exceptions.AutoGraphBusyError`
   A conflicting job is already running on the project. Wait for it and
   retry.

:exc:`~arango_ai_sdk.exceptions.IngestionFailedError`
   A build or strategy run ended as failed, or the import ended as failed or
   cancelled. ``job_status`` on the exception is that step's final status;
   its type tells you which step it was.

:exc:`~arango_ai_sdk.exceptions.JobTimeoutError`
   The shared ``timeout`` ran out, either while waiting on a step or before
   the next step could start. The step that was running keeps going on the
   platform.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

When a later step fails, the earlier ones have completed and their results
are stored on the platform. Rerun the failed step on its own rather than the
whole ``ingest``: a second ``ingest`` would refuse at the build with
:exc:`~arango_ai_sdk.exceptions.CategoryAlreadyBuiltError` unless you pass
``incremental=True``.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import IngestionFailedError

   sales = client.project.get(project_name="sales")

   def show(progress):
       print(progress.step, progress.status.status)

   try:
       result = sales.autograph.ingest(
           categories=["legal", "finance"],
           timeout=3600.0,
           on_progress=show,
       )
   except IngestionFailedError as exc:
       print(f"Ingestion failed: {exc}")
   else:
       print(f"{result.build.document_count} documents in the corpus")
       print(f"strategies: {dict(result.strategies.strategy_type_counts)}")
       if result.orchestration is None:
           print("Graph already up to date")
       else:
           imported = sum(1 for job in result.orchestration.jobs if job.imported)
           print(
               f"Imported {imported} partitions, "
               f"skipped {result.orchestration.skipped_jobs}"
           )
