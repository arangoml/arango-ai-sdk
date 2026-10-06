.. _autograph-strategize:

Choosing a strategy per cluster
===============================

.. code-block:: python

   run = sales.autograph.strategize(categories=["legal", "finance"])

One call starts the strategizer for the given categories, waits until it
finishes and returns the final job status. The strategizer looks at each
cluster the corpus build produced and decides how it is imported: as a full
knowledge graph with entities and relations (``FullGraphRAG``), or as vectors
only (``VectorRAG``). The choice is stored on the platform; the import step
reads it from there. This is the second step of ingestion, after
:ref:`autograph-corpus-build` and before :ref:`autograph-orchestrate`.

The status this call returns carries progress counts only. Which cluster got
which strategy is read separately with :ref:`autograph-strategies`.

Before sending anything, ``strategize`` reloads the project and refuses if it
has no AutoGraph service.

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
     - The categories to analyse, as passed to the corpus build. At least one
       is required.
   * - ``complexity``
     - :class:`~arango_ai_sdk.models.RagStrategizerComplexity`
     - What share of the clusters, ranked by complexity, gets ``FullGraphRAG``
       rather than ``VectorRAG``: ``very_low`` none, ``low`` a quarter,
       ``moderate`` half, ``high`` three quarters, ``very_high`` all. Default
       ``high``, so a corpus with a single cluster still gets one knowledge
       graph.
   * - ``extract_images_default``
     - ``bool``
     - Turn image extraction on for the ``FullGraphRAG`` clusters. Accepted
       only with ``complexity`` ``high`` or ``very_high``; the service rejects
       it otherwise. Default ``False``. ``VectorRAG`` clusters never extract
       images.
   * - ``max_parallel_clusters``
     - ``int``, optional
     - How many clusters are analysed at once. Unset uses the service default.
   * - ``timeout``
     - ``float``, optional
     - Deadline in seconds for the whole run. Unset waits without bound.
   * - ``poll_interval``
     - ``float``
     - Seconds between two status polls. Default 30.
   * - ``on_progress``
     - callable, optional
     - Called with every polled
       :class:`~arango_ai_sdk.models.GetRagStrategizerJobStatusResponse`. See
       :ref:`autograph-waiting`.

Return value
------------

The final :class:`~arango_ai_sdk.models.GetRagStrategizerJobStatusResponse`.
Its ``status`` is ``"completed"`` and ``progress`` is the percentage done,
0 to 100. Nothing on it says which strategy a cluster got; call
``strategies()`` for that.

Errors
------

:exc:`ValueError`
   ``categories`` is empty. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError`
   The project has no AutoGraph service. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.ModelConfigNotReadyError`
   AutoGraph cannot use its chat or embedding settings. Check the secret
   profiles and models passed to ``deploy``, or retry shortly.

:exc:`~arango_ai_sdk.exceptions.AutoGraphBusyError`
   A conflicting job is already running on the project. Wait for it and
   retry.

:exc:`~arango_ai_sdk.exceptions.IngestionFailedError`
   The run ended as failed. ``job_status`` on the exception is the final
   status. Cancellation only happens on an import.

:exc:`~arango_ai_sdk.exceptions.JobStatusLostError`
   AutoGraph no longer has a status for the run, usually after a restart. The
   run itself may still be going.

:exc:`~arango_ai_sdk.exceptions.JobTimeoutError`
   ``timeout`` passed before the run finished. The run keeps going on the
   platform.

Any other failure, including ``extract_images_default`` with a complexity
below ``high``, surfaces as one of the general SDK exceptions described in
:ref:`errors`, usually a :exc:`~arango_ai_sdk.exceptions.ServiceError`
carrying the status code and message the service returned.

Example
-------

.. code-block:: python

   from arango_ai_sdk.models import RagStrategizerComplexity

   sales = client.project.get(project_name="sales")

   def show(status):
       print(f"strategize {status.status} {status.clusters_done}/{status.clusters_total}")

   run = sales.autograph.strategize(
       categories=["legal", "finance"],
       complexity=RagStrategizerComplexity.moderate,
       on_progress=show,
   )
   stored = sales.autograph.strategies()
   print(f"{run.clusters_done} clusters analysed: {dict(stored.strategy_type_counts)}")
