.. _projects-create:

Creating a project
==================

.. code-block:: python

   project = client.project.create(
       project_name="my_project",
       project_type="autograph",
       description="Optional free text.",
   )

One call creates the project in the client's database and returns an
:class:`~arango_ai_sdk.projects.AiProjectHandle` bound to it.

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
     - Name of the project. May contain letters, digits, underscores and hyphens only.
   * - ``project_type``
     - ``str``
     - Kind of project to create, for example ``"autograph"``.
   * - ``description``
     - ``str``, optional
     - Free-text description. Keyword-only. Omitted entirely when not given.

The database is not a parameter: the project is created in the ``db_name`` the
client was constructed with.

Return value
------------

An :class:`~arango_ai_sdk.projects.AiProjectHandle` with ``name``, ``project_type``,
``db_name`` and ``description`` set from the created project. See
:ref:`projects` for the property descriptions.

Errors
------

:exc:`~arango_ai_sdk.exceptions.InvalidProjectNameError`
   The name was rejected: it is empty, too long, or contains characters outside
   letters, digits, underscores and hyphens.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`, for example
:exc:`~arango_ai_sdk.exceptions.PlatformUnreachableError` if the deployment
could not be reached, or :exc:`~arango_ai_sdk.exceptions.ServiceError`
carrying the status code and message the service returned.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import InvalidProjectNameError

   try:
       project = client.project.create(
           project_name="my project",   # a space is not allowed
           project_type="autograph",
       )
   except InvalidProjectNameError as exc:
       print(f"Choose another name: {exc}")
   else:
       print(f"Created {project.name} in {project.db_name}")
