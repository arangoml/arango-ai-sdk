AutoRAG
=======

You do not construct these classes yourself. Every
:class:`~arango_ai_sdk.AiProjectHandle` owns one
:class:`~arango_ai_sdk.managers.autorag_manager.AutoRagManager` and exposes it as
``autorag``. ``deploy``, ``list`` and ``get`` hand back an
:class:`~arango_ai_sdk.managers.autorag.AutoRag` bound to one retriever.
``deploy`` returns an
:class:`~arango_ai_sdk.managers.autorag_manager.AutoRagDeployResult`, whose
``service_info`` is a :class:`~arango_ai_sdk.models.ServiceInfo` documented
in :doc:`models` and whose ``autorag`` is the bound object. ``undeploy``
returns the ``ServiceInfo`` directly. ``ask`` returns a
:class:`~arango_ai_sdk.models.GraphRagQueryResponse`.

.. autoclass:: arango_ai_sdk.managers.autorag_manager.AutoRagManager
   :members: deploy, list, get

.. autoclass:: arango_ai_sdk.managers.autorag_manager.AutoRagDeployResult

.. autoclass:: arango_ai_sdk.managers.autorag.AutoRag
   :members: service_id, is_deployed, service_url, service_path, ask, wait_until_ready, undeploy

.. autoclass:: arango_ai_sdk.managers.autorag.AutoRagHealthState
   :members:
   :undoc-members:
