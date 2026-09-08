.. _projects:

Projects
========

A project is the unit everything else in the AI Suite happens in. Uploaded
documents, the context graph built from them, and the questions asked against
it all belong to one project. Creating a project is therefore the first thing
you do after constructing a client.

The projects area is the ``project`` namespace on the client:

.. code-block:: python

   project = client.project.create(project_name="my_project", project_type="autograph")

.. toctree::
   :maxdepth: 1

   create

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
   * - List, get, update or delete a project
     - Not yet available
     - Arrives in a later release.

The returned project
--------------------

Operations that return a project return an
:class:`~arango_ai_sdk.models.AiProject`. Create sets these attributes:

``project_name``
   The project's name.

``project_type``
   The project's type, for example ``"autograph"``.

``project_db_name``
   The database the project is stored in. This is the client's ``db_name``.

``project_description``
   The description, or ``None`` if none was given.

The class has further attributes (``project_metadata``, ``project_files``,
``model_settings``) that describe a project's later state. Create leaves them
at their empty defaults; they are filled by operations that arrive in a later
release.
