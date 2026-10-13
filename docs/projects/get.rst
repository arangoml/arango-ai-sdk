.. _projects-get:

Getting a project
=================

.. code-block:: python

   project = client.project.get(project_name="my_project")

Fetches a project that already exists in the client's database, by name, and
returns an :class:`~arango_ai_sdk.projects.AiProjectHandle` bound to it. Use it to pick
up work on a project created earlier, in a previous run or through the
platform UI.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 22 18 60

   * - Parameter
     - Type
     - Meaning
   * - ``project_name``
     - ``str``
     - Name of the project.

The database is not a parameter: the project is looked up in the ``db_name``
the client was constructed with.

Return value
------------

An :class:`~arango_ai_sdk.projects.AiProjectHandle`. Unlike create, get returns the
project's full current state, so ``metadata``, ``files`` and ``model_settings``
are filled where the platform has them. See :ref:`projects` for the property
descriptions.

Errors
------

:exc:`~arango_ai_sdk.exceptions.ProjectNotFoundError`
   No project with this name exists in the client's database, or
   ``project_name`` is empty.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import ProjectNotFoundError

   try:
       project = client.project.get(project_name="does_not_exist")
   except ProjectNotFoundError:
       print("Create the project first.")
   else:
       print(project.name, project.project_type)
