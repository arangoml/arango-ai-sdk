.. _autograph-orchestrate:

Importing the graph
===================

.. code-block:: python

   orchestration = sales.autograph.orchestrate(categories=["legal", "finance"])

One call starts the import for the given categories, waits until it finishes
and returns the final status. The import, called orchestration on the
platform, turns each cluster into its part of the context graph using the
strategy the strategizer chose for it: entities and relations for a
``FullGraphRAG`` cluster, chunks and embeddings for a ``VectorRAG`` one. This
is the last step of ingestion, after :ref:`autograph-corpus-build` and
:ref:`autograph-strategize`.

Only clusters whose data changed since the last import are processed. When
nothing changed, the platform has nothing to do and ``orchestrate`` returns
``None`` right away. That is success, not an error.

The chat and embedding secret profiles the import needs come from the
project's model settings, which ``deploy`` stored. Before sending anything,
``orchestrate`` reloads the project and refuses if it has no AutoGraph service
or no secret profile IDs in its model settings.

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
     - The categories to import, as passed to the corpus build. At least one
       is required.
   * - ``timeout``
     - ``float``, optional
     - Deadline in seconds for the whole run. Unset waits without bound.
   * - ``poll_interval``
     - ``float``
     - Seconds between two status polls. Default 30.
   * - ``on_progress``
     - callable, optional
     - Called with every polled
       :class:`~arango_ai_sdk.models.GetOrchestrationStatusResponse`. See
       :ref:`autograph-waiting`.

Return value
------------

The final :class:`~arango_ai_sdk.models.GetOrchestrationStatusResponse`, or
``None`` when every category was already up to date.

``status`` describes the whole run and is ``"completed"`` on return. It
reaches that value once every import job has finished and the partitions the
jobs reported writing are present in the graph. If the knowledge-graph check
itself fails, ``output_verified`` stays unset and that is reported in
``message``; it is not treated as an import failure. On a returned status
``unverified_partitions`` is empty. A partition the check cannot find in the
graph forces the run to fail, so it shows up on
:exc:`~arango_ai_sdk.exceptions.IngestionFailedError`'s
``job_status.unverified_partitions``.

``phase`` says where a running import is, and is the field to show as
progress inside ``on_progress``: ``initializing``, ``starting_importers``,
``importing``, ``verifying``, then ``finished``. An import that has been
running for a while in ``starting_importers`` has not imported anything yet.

The job counts (``total_jobs``, ``completed_jobs``, ``failed_jobs``,
``running_jobs``, ``pending_jobs``, ``skipped_jobs``) and ``jobs``, one entry
per partition, break the run down. One category can have more than one job.
``completed_jobs`` includes jobs that finished without importing. Each job
has ``strategy_type``, ``status``, ``category``, ``error_message``,
``entities_added`` and ``imported``. Read ``imported`` and ``skipped_jobs``
to tell a real import from a skip. ``entities_added`` sums what the
``FullGraphRAG`` jobs wrote; a ``VectorRAG`` partition writes no entities, so
zero is not evidence that nothing was imported.

Errors
------

:exc:`ValueError`
   ``categories`` is empty. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError`
   The project has no AutoGraph service. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.ServiceError`
   The project's model settings hold no chat or embedding secret profile ID,
   so the import could not be started. Nothing was sent. That happens on a
   first deploy that did not include both model names and both profile IDs.
   A later deploy keeps settings already stored, including their profile IDs,
   even when the new install omits the model names. See
   :ref:`autograph-deploy`.

:exc:`~arango_ai_sdk.exceptions.ModelConfigNotReadyError`
   AutoGraph cannot use its chat or embedding settings. Check the secret
   profiles and models passed to ``deploy``, or retry shortly.

:exc:`~arango_ai_sdk.exceptions.AutoGraphBusyError`
   Another build, strategizer run, orchestration or delete is in progress for
   the project. Wait for it and retry.

:exc:`~arango_ai_sdk.exceptions.NoStrategiesError`
   No strategy is stored for the categories. Run :ref:`autograph-strategize`
   first.

:exc:`~arango_ai_sdk.exceptions.IngestionFailedError`
   The run ended as failed or cancelled. ``job_status`` on the exception is
   the final status; its ``jobs`` say which partitions failed and why.

:exc:`~arango_ai_sdk.exceptions.JobStatusLostError`
   AutoGraph no longer has a status for the run, usually after a restart. The
   run itself may still be going.

:exc:`~arango_ai_sdk.exceptions.JobTimeoutError`
   ``timeout`` passed before the run finished. The run keeps going on the
   platform.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import IngestionFailedError, NoStrategiesError

   sales = client.project.get(project_name="sales")

   def show(status):
       print(f"orchestrate {status.phase} {status.completed_jobs}/{status.total_jobs}")

   try:
       orchestration = sales.autograph.orchestrate(
           categories=["legal", "finance"],
           on_progress=show,
       )
   except NoStrategiesError:
       print("Run strategize first.")
   except IngestionFailedError as exc:
       for job in exc.job_status.jobs:
           if job.error_message:
               print(f"{job.category}/{job.rag_partition_id}: {job.error_message}")
   else:
       if orchestration is None:
           print("Nothing to import; the graph is up to date.")
       else:
           imported = sum(1 for job in orchestration.jobs if job.imported)
           print(
               f"Imported {imported} partitions, "
               f"skipped {orchestration.skipped_jobs}"
           )
