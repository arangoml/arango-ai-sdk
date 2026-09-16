.. _autograph-undeploy:

Removing AutoGraph
==================

.. code-block:: python

   removed = sales.autograph.undeploy()

One call stops and removes the project's AutoGraph service and returns the
service record as the platform last described it. There is nothing to pass:
the project has one AutoGraph service, and ``undeploy`` reloads the project to
find it.

Parameters
----------

None.

Return value
------------

A :class:`~arango_ai_sdk.models.ServiceInfo` for the removed service.

The handle is reloaded after the call, so ``sales.autograph.is_deployed`` is
``False`` and ``sales.autograph.service_id`` is ``None``.

Errors
------

:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError`
   The project has no AutoGraph service. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.ProjectNotFoundError`
   The project no longer exists on the platform.

:exc:`~arango_ai_sdk.exceptions.ServiceNotFoundError`
   The project record still names a service, but the platform no longer knows
   it. Call ``sales.refresh()`` and check ``is_deployed`` again.

:exc:`~arango_ai_sdk.exceptions.ServiceNotDeletableError`
   The platform will not remove this service because another entity manages
   it.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import AutoGraphNotDeployedError

   sales = client.project.get(project_name="sales")
   try:
       sales.autograph.undeploy()
   except AutoGraphNotDeployedError:
       print("Nothing to remove.")
   else:
       print("AutoGraph removed; redeploy with sales.autograph.deploy(...)")
