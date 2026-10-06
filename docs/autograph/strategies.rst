.. _autograph-strategies:

Reading the stored strategies
=============================

.. code-block:: python

   stored = sales.autograph.strategies()

One call returns the strategy the strategizer chose for each cluster, as
stored on the platform. It reads; it starts no run and waits for nothing. Call
it after :ref:`autograph-strategize` has finished, or any time later to see
what the import will use.

Before sending anything, ``strategies`` reloads the project and refuses if it
has no AutoGraph service.

Parameters
----------

None.

Return value
------------

A :class:`~arango_ai_sdk.models.GetRagStrategizerStrategyResponse` with three
attributes:

``strategies``
   One entry per cluster. Each has ``cluster_id``, ``strategy_type``
   (``"FullGraphRAG"`` or ``"VectorRAG"``), ``rag_partition_id``, the
   ``entity_types`` the strategizer expects to find, ``document_count`` and a
   ``parameters`` mapping of further settings.

``total_strategies``
   How many entries there are.

``strategy_type_counts``
   How many clusters got each strategy type, keyed by type name.

Before the strategizer has run for the project, the list is empty and the
counts are zero. The import step refuses to run on such a project with
:exc:`~arango_ai_sdk.exceptions.NoStrategiesError`.

Errors
------

:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError`
   The project has no AutoGraph service. Nothing was sent.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   sales = client.project.get(project_name="sales")
   stored = sales.autograph.strategies()
   for strategy in stored.strategies:
       print(f"{strategy.cluster_id}: {strategy.strategy_type}, {strategy.document_count} documents")
