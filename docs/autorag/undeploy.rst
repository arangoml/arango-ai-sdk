.. _autorag-undeploy:

Removing a retriever
====================

.. code-block:: python

   removed = retriever.undeploy()

One call stops and removes this retriever and returns the service record as
the platform last described it. There is nothing to pass: the object is
already bound to one service id, and ``undeploy`` reloads the project to
confirm that id is still there.

Other retrievers in the project are left in place. So is the context graph,
and so is the project's AutoGraph service. To remove that as well, call
``sales.autograph.undeploy()``. See :ref:`autograph-undeploy`.

Parameters
----------

None.

Return value
------------

A :class:`~arango_ai_sdk.models.ServiceInfo` for the removed retriever.

The handle is reloaded after the call, so ``retriever.is_deployed`` is
``False``. ``retriever.service_id`` is unchanged: it is the id this object
was bound to, not a live lookup. ``sales.autorag.list()`` no longer includes
it. ``sales.autorag.get`` with that id raises
:exc:`~arango_ai_sdk.exceptions.AutoRagNotDeployedError`.

Errors
------

:exc:`~arango_ai_sdk.exceptions.AutoRagNotDeployedError`
   The project has no retriever with this object's service id. Nothing was
   sent.

:exc:`~arango_ai_sdk.exceptions.ServiceNotFoundError`
   The project record still names the service, but the platform no longer
   knows it. Call ``sales.refresh()`` and check ``is_deployed`` again.

:exc:`~arango_ai_sdk.exceptions.ServiceNotDeletableError`
   The platform will not remove this service because another entity manages
   it.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import AutoRagNotDeployedError

   try:
       removed = retriever.undeploy()
   except AutoRagNotDeployedError:
       print("Nothing to remove.")
   else:
       print(f"Removed {removed.service_id}")
