AutoGraph
=========

You do not construct this class yourself. Every
:class:`~arango_ai_sdk.AiProjectHandle` owns one
:class:`~arango_ai_sdk.autograph.AutoGraph` and exposes it as ``autograph``.
It is bound to that handle's project and shares the client's connection.
``deploy`` and ``undeploy`` return a :class:`~arango_ai_sdk.models.ServiceInfo`,
documented in :doc:`models`.

.. autoclass:: arango_ai_sdk.autograph.AutoGraph
   :members: is_deployed, service_id, service_url, deploy, undeploy
