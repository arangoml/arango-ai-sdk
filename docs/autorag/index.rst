.. _autorag:

AutoRAG
=======

AutoRAG is how you ask questions against a project's context graph. A
retriever is a platform-managed service inside the project. Unlike AutoGraph,
a project can run more than one, each with its own models and secret profiles.

The AutoRAG area is the ``autorag`` object on a project handle, not a
namespace on the client, because a retriever belongs to one project. Create
or get the project, deploy a retriever, then ask it:

.. code-block:: python

   sales = client.project.get(project_name="sales")
   deployed = sales.autorag.deploy(
       chat_api_provider="openai",
       embedding_api_provider="openai",
       chat_secret_profile_id=chat.profile_id,
       embedding_secret_profile_id=embed.profile_id,
       chat_model="gpt-4o",
       embedding_model="text-embedding-3-small",
   )
   retriever = deployed.autorag
   if retriever.wait_until_ready():
       answer = retriever.ask("What do the contracts say about renewal?")
       print(answer.result)
   retriever.undeploy()

Deploy a retriever only after the project has a context graph. Create the
project and the chat and embedding secret profiles first, deploy AutoGraph,
upload the documents and ingest them. See :ref:`projects`,
:ref:`secret-profiles`, :ref:`files` and :ref:`autograph`.

.. toctree::
   :maxdepth: 1

   deploy
   list-and-get
   ask
   undeploy

Available operations
--------------------

.. list-table::
   :header-rows: 1
   :widths: 34 18 48

   * - Operation
     - Status
     - Page
   * - Deploy a retriever into the project
     - Available
     - :ref:`autorag-deploy`
   * - List the project's retrievers
     - Available
     - :ref:`autorag-list-and-get`
   * - Look up one retriever by service id
     - Available
     - :ref:`autorag-list-and-get`
   * - Ask a question
     - Available
     - :ref:`autorag-ask`
   * - Wait until a retriever is serving
     - Available
     - :ref:`autorag-deploy`
   * - Remove one retriever
     - Available
     - :ref:`autorag-undeploy`
   * - Stream an answer, or read past query runs
     - Not yet available
     - The service has those endpoints. ``ask`` is the one call the SDK
       makes.

One manager, many retrievers
----------------------------

``sales.autorag`` is a manager, not a retriever. ``deploy`` installs a new
one and hands back an :class:`~arango_ai_sdk.autorag.AutoRag` bound to that
service for the object's lifetime. ``list`` and ``get`` hand back the ones
already in the project. Asking, waiting and removing happen on that object,
not on the manager: there is no ``sales.autorag.ask``.

Deploying a second retriever does not replace the first. Each keeps its own
models and secret profiles. Removing one leaves the others in place.

The deployment state
--------------------

An ``AutoRag`` reads its state from the project record the handle holds. It
never sends a request for that, so reading these is free:

``service_id``
   The platform's ID of this retriever. Fixed when the object was created.

``is_deployed``
   ``True`` when the last project snapshot still lists that id.

``service_url``
   Where the service listens inside the platform, or ``None`` when it is
   gone. This is an in-cluster address, not a URL you open in a browser.

``service_path``
   ``service_url`` without scheme and host, or ``None``. The SDK appends the
   query and health endpoints to it. You do not.

Every method reloads the project before it acts, and ``deploy`` and
``undeploy`` also after they finish, so the state is current right after any
call. Reading ``is_deployed`` on its own does not reload. To pick up a
change made elsewhere, for example a deploy from another client, call
``sales.refresh()`` on the handle, or ``list`` / ``get``, which reload for
you.
