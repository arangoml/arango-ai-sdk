AutoGraph
=========

You do not construct this class yourself. Every
:class:`~arango_ai_sdk.AiProjectHandle` owns one
:class:`~arango_ai_sdk.projects.services.autograph.service.AutoGraph` and exposes it as ``autograph``.
It is bound to that handle's project and shares the client's connection.
``deploy`` returns a :class:`~arango_ai_sdk.projects.services.autograph.service.DeployResult`, whose
``service_info`` is a :class:`~arango_ai_sdk.models.ServiceInfo` documented in
:doc:`models`; ``undeploy`` returns the ``ServiceInfo`` directly. The
ingestion methods return the status classes documented in :doc:`models`;
``ingest`` wraps them in an :class:`~arango_ai_sdk.projects.services.autograph.service.IngestResult`.

.. autoclass:: arango_ai_sdk.projects.services.autograph.service.AutoGraph
   :members: is_deployed, service_id, service_url, service_path, deploy, wait_until_ready, undeploy, ingest, corpus_build, strategize, strategies, orchestrate

.. autoclass:: arango_ai_sdk.projects.services.autograph.service.DeployResult

.. autoclass:: arango_ai_sdk.projects.services.autograph.service.IngestResult

.. autoclass:: arango_ai_sdk.projects.services.autograph.service.IngestProgress

.. autoclass:: arango_ai_sdk.projects.services.autograph.service.JobState
   :members:
   :undoc-members:
