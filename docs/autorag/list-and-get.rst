.. _autorag-list-and-get:

Listing and looking up retrievers
=================================

``list`` and ``get`` do not install anything. Both reload the project and
hand back an :class:`~arango_ai_sdk.projects.services.autorag.service.AutoRag` for each retriever the
project record already names. The record is the source of truth: a retriever
another client removed is absent after the reload, and one another client
deployed is present.

Listing them
------------

.. code-block:: python

   retrievers = sales.autorag.list()
   for retriever in retrievers:
       print(retriever.service_id, retriever.is_deployed)

No parameters. Returns a list, one object per deployed retriever, in the
order the project record holds them. A project with none returns an empty
list. That is not an error.

Each object's ``is_deployed`` is ``True`` at the moment ``list`` returns,
because the list was just read from a fresh snapshot. It can become ``False``
later if something else removes that retriever; the object keeps its
``service_id`` either way.

Looking one up
--------------

.. code-block:: python

   retriever = sales.autorag.get(deployed.service_info.service_id)

.. list-table::
   :header-rows: 1
   :widths: 20 16 64

   * - Parameter
     - Type
     - Meaning
   * - ``service_id``
     - ``str``
     - Platform ID of the retriever. This is ``service_info.service_id`` from
       :ref:`autorag-deploy`, or ``service_id`` on an object from ``list``.

Returns the :class:`~arango_ai_sdk.projects.services.autorag.service.AutoRag` bound to that id.

Errors
------

``list`` has none of its own. A project that cannot be reloaded surfaces as
one of the general SDK exceptions described in :ref:`errors`.

:exc:`~arango_ai_sdk.exceptions.AutoRagNotDeployedError`
   ``get`` was given an id the project does not have. Nothing was sent to a
   retriever. The same exception is what :ref:`autorag-ask` and
   :ref:`autorag-undeploy` raise later, if the retriever disappears between
   this call and those.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import AutoRagNotDeployedError

   sales = client.project.get(project_name="sales")
   ids = [retriever.service_id for retriever in sales.autorag.list()]
   print("retrievers:", ids)
   try:
       same = sales.autorag.get(ids[0])
   except AutoRagNotDeployedError:
       print("That retriever is gone.")
   except IndexError:
       print("This project has no retriever yet.")
   else:
       print(same.service_id, same.is_deployed)
