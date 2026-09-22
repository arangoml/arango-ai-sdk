.. _autograph:

AutoGraph
=========

AutoGraph is the service that turns a project's documents into a context graph.
It runs as a platform-managed service inside
the project, and a project has exactly one instance of it.

The AutoGraph area is the ``autograph`` object on a project handle, not a
namespace on the client, because AutoGraph belongs to one project. Create or
get the project, then work on ``autograph``:

.. code-block:: python

   sales = client.project.get(project_name="sales")
   info = sales.autograph.deploy(
       chat_api_provider="openai",
       embedding_api_provider="openai",
       chat_secret_profile_id=chat.profile_id,
       embedding_secret_profile_id=embed.profile_id,
       fps_recovery_username="fps-recovery",
   )
   sales.autograph.is_deployed   # True
   sales.autograph.undeploy()

Create the project and the chat and embedding secret profiles first; deploy
takes the profile IDs. See :ref:`projects` and :ref:`secret-profiles`.

.. toctree::
   :maxdepth: 1

   deploy
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
   * - Remove the project's AutoGraph
     - Available
     - :ref:`autograph-undeploy`
   * - Build the graph: corpus build, strategizer
     - Not yet available
     - Arrive in later releases as further methods on ``autograph``.

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

``deploy`` and ``undeploy`` reload the project before they act and after they
finish, so the state is current right after either call. To pick up a change
made elsewhere, for example a deploy from another client, call
``sales.refresh()`` on the handle.

One AutoGraph per project
-------------------------

A project holds one AutoGraph service. ``deploy`` reloads the project and
refuses with :exc:`~arango_ai_sdk.exceptions.AutoGraphAlreadyDeployedError`
when one is already there, whichever client deployed it. ``undeploy`` needs no
service ID for the same reason: it removes the one the project has, or raises
:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError` when there is none.
