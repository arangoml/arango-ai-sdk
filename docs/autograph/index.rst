.. _autograph:

AutoGraph
=========

AutoGraph is the service that turns a project's documents into a context graph.
It runs as a platform-managed service inside
the project, and a project has exactly one instance of it.

The AutoGraph area is the ``autograph`` object on a project handle, not a
namespace on the client, because AutoGraph belongs to one project. Create or
get the project, then work on ``autograph``: deploy the service once, then
ingest the files uploaded under the project's categories.

.. code-block:: python

   sales = client.project.get(project_name="sales")
   sales.autograph.deploy(
       chat_api_provider="openai",
       embedding_api_provider="openai",
       chat_secret_profile_id=chat.profile_id,
       embedding_secret_profile_id=embed.profile_id,
       fps_recovery_username="fps-recovery",
       chat_model="gpt-4o",
       embedding_model="text-embedding-3-small",
   )
   if sales.autograph.wait_until_ready():
       result = sales.autograph.ingest(categories=["legal", "finance"])
   sales.autograph.undeploy()

Create the project and the chat and embedding secret profiles first. Deploy
takes the profile IDs and both model names. Upload the documents before
ingesting. See
:ref:`projects`, :ref:`secret-profiles` and :ref:`files`.

.. toctree::
   :maxdepth: 1

   deploy
   ingest
   corpus-build
   strategize
   strategies
   orchestrate
   undeploy

Available operations
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Operation
     - Status
     - Page
   * - Deploy AutoGraph into the project
     - Available
     - :ref:`autograph-deploy`
   * - Ingest: build, strategize and import in one call
     - Available
     - :ref:`autograph-ingest`
   * - Build the corpus
     - Available
     - :ref:`autograph-corpus-build`
   * - Choose a strategy per cluster
     - Available
     - :ref:`autograph-strategize`
   * - Read the stored strategies
     - Available
     - :ref:`autograph-strategies`
   * - Import the graph
     - Available
     - :ref:`autograph-orchestrate`
   * - Remove the project's AutoGraph
     - Available
     - :ref:`autograph-undeploy`
   * - Delete categories or files from the graph
     - Not yet available
     - Arrives in a later release as further methods on ``autograph``.

Ingestion in three steps
------------------------

Ingestion takes the files uploaded under a project's categories and turns
them into the context graph. It runs in three steps on the platform, and each
is a method on ``autograph`` that starts the step, waits for it and returns
its final status:

1. :ref:`autograph-corpus-build` reads the files, extracts their text, links
   similar documents and groups them into clusters.
2. :ref:`autograph-strategize` decides for every cluster whether it becomes a
   full knowledge graph or vectors only, and stores that choice.
   :ref:`autograph-strategies` reads the stored choices back.
3. :ref:`autograph-orchestrate` imports each cluster according to its
   strategy. Clusters that did not change since the last import are skipped.

:ref:`autograph-ingest` runs the three in order and returns all their
results. Use it when you want the graph and nothing in between; call the
steps yourself to inspect the corpus first, to pass options ``ingest`` does
not expose, or to redo a single step.

Categories
----------

Every ingestion method takes ``categories``. A category is the second label
of the scope a file was uploaded with: the first label is the project name,
the second the category. Files uploaded with ``scope=["sales", "legal"]``
belong to category ``"legal"`` of project ``sales``.

.. code-block:: python

   client.files.upload_folder("./contracts", scope=["sales", "legal"])
   client.files.upload_folder("./reports", scope=["sales", "finance"])
   sales.autograph.ingest(categories=["legal", "finance"])

Building a category a second time is refused unless you say so: pass
``incremental=True`` to add files uploaded since the last build. See
:ref:`autograph-corpus-build`.

.. _autograph-waiting:

Waiting for a step
------------------

The ingestion methods do not return until their step is finished. They poll
the step's status on the platform and share three parameters for that:

``timeout``
   Deadline in seconds. Unset waits for as long as the step takes. When it
   passes, the method raises :exc:`~arango_ai_sdk.exceptions.JobTimeoutError`;
   the step itself keeps running on the platform, only the SDK stopped
   waiting. On ``ingest`` the deadline covers all steps together.

``poll_interval``
   Seconds between two polls. Default 30. A smaller value shows progress
   sooner at the cost of more requests.

``on_progress``
   A callable the method invokes with every status it polls, so you can print
   or log progress. It is called from inside the method, on the same thread,
   so keep it quick.

A build or a strategy run that ends as failed, or an import that ends as
failed or cancelled, raises
:exc:`~arango_ai_sdk.exceptions.IngestionFailedError`, which carries the final
status as ``job_status``. If the platform loses track of a step while you
wait, usually because the service restarted, the method raises
:exc:`~arango_ai_sdk.exceptions.JobStatusLostError`; the step may still be
running. Three failed polls in a row raise the last communication error,
usually :exc:`~arango_ai_sdk.exceptions.ServiceError` or
:exc:`~arango_ai_sdk.exceptions.PlatformUnreachableError`.

Conflicting jobs
----------------

AutoGraph refuses to start a job while a conflicting one is running on the
project. Starting it anyway raises
:exc:`~arango_ai_sdk.exceptions.AutoGraphBusyError` before anything is
started. Which jobs conflict depends on the call. Since the SDK methods
wait for their step, this happens when another client or another thread
started a job on the same project, or when an earlier call stopped waiting
with
:exc:`~arango_ai_sdk.exceptions.JobTimeoutError` or
:exc:`~arango_ai_sdk.exceptions.JobStatusLostError` while its job kept
running.

The deployment state
--------------------

``autograph`` reads its state from the project record the handle holds. It
never sends a request for that, so reading these is free:

``is_deployed``
   ``True`` when the project has an AutoGraph service.

``service_id``
   The platform's ID of that service, or ``None`` when nothing is deployed.

``service_url``
   Where the service listens inside the platform, or ``None``.

Every method on ``autograph`` reloads the project before it acts, and
``deploy`` and ``undeploy`` also after they finish, so the state is current
right after any call. To pick up a change made elsewhere, for example a deploy
from another client, call ``sales.refresh()`` on the handle.

One AutoGraph per project
-------------------------

A project holds one AutoGraph service. ``deploy`` reloads the project and
refuses with :exc:`~arango_ai_sdk.exceptions.AutoGraphAlreadyDeployedError`
when one is already there, whichever client deployed it. ``undeploy`` needs no
service ID for the same reason: it removes the one the project has, or raises
:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError` when there is none.
The ingestion methods raise the same error on a project without a service.

Asking a question
-----------------

Once the graph is imported, questions go through a retriever on the same
project handle, not through ``autograph``. See :ref:`autorag`.
