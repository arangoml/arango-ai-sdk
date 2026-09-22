.. _projects:

Projects
========

A project is the unit everything else in the AI Suite happens in. Uploaded
documents, the context graph built from them, and the questions asked against
it all belong to one project. Creating or fetching a project is therefore the
first thing you do after constructing a client.

The projects area is the ``project`` namespace on the client. Its operations
return a :class:`~arango_ai_sdk.AiProjectHandle`, and everything project-scoped
happens on that handle:

.. code-block:: python

   sales = client.project.create(project_name="sales", project_type="autograph")
   support = client.project.get(project_name="support")

.. toctree::
   :maxdepth: 1

   create
   get

Available operations
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Operation
     - Status
     - Page
   * - Create a project
     - Available
     - :ref:`projects-create`
   * - Get an existing project by name
     - Available
     - :ref:`projects-get`
   * - List, update or delete a project
     - Not yet available
     - Arrives in a later release.

The project handle
------------------

Create and get return an :class:`~arango_ai_sdk.AiProjectHandle`. You never
construct one yourself. A handle is bound to one project and shares the
client's connection, so any number of handles can live under one client
without signing in again.

The handle exposes the project record as read-only properties:

``name``
   The project's name.

``project_type``
   The project's type, for example ``"autograph"``.

``db_name``
   The database the project is stored in. This is the client's ``db_name``.

``description``
   The description, or ``None`` if none was given.

``metadata``, ``files``, ``model_settings``
   The project's later state: registered services, uploaded files and the
   AutoGraph model configuration. Empty on a freshly created project;
   ``metadata`` and ``model_settings`` are filled once AutoGraph is deployed.

``project``
   The raw :class:`~arango_ai_sdk.models.AiProject` record, for users who
   want the platform's object itself.

The handle also carries the project-scoped areas and one method:

``autograph``
   The project's AutoGraph service: deploy it, remove it, read whether it is
   deployed. One per project. See :ref:`autograph`.

``refresh()``
   Reload the project record from the platform and return it. The properties
   above read from that record, so call ``refresh()`` to see changes made
   elsewhere, for example a service deployed from another client.
   ``autograph.deploy`` and ``undeploy`` call it for you.

Later releases attach further project-scoped areas to the handle, such as AutoRag,
without changing the client.
