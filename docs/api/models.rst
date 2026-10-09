Models
======

.. automodule:: arango_ai_sdk.models

The classes below are the ones the SDK returns or accepts. Import them from
``arango_ai_sdk.models``; that path stays stable even if the classes' origin
changes.

.. code-block:: python

   from arango_ai_sdk.models import AiProject, Profile, ProfileType, ServiceInfo
   from arango_ai_sdk.models import RagStrategizerComplexity

You construct none of these yourself. ``AiProject``, ``Profile``,
``ServiceInfo`` and the ingestion status classes come back from SDK calls;
``RagStrategizerComplexity`` and ``QueryType`` are the enums you pass in.
``CreateProjectRequest``, ``CreateSecretProfileRequest`` and
``CreateEntityRequest`` are data classes those calls fill; you still pass
arguments on ``create`` and ``deploy``, not those objects.

``create`` fills a request data class and sends ``to_dict()``. Field names come
from the proto, so a rename fails at import time, not on the wire. ``to_dict``
emits camelCase keys, which the gateway accepts. A plain string at its zero
value is omitted; the server reads a missing field as empty, so an empty name
is still rejected. Optional fields (``project_description``, ``description``,
``provider``) track presence: ``None`` is omitted, ``""`` is sent as ``""``.

Projects
--------

.. py:class:: arango_ai_sdk.models.AiProject

   A project as the platform returned it. Wrapped by
   :class:`~arango_ai_sdk.AiProjectHandle` and reachable as ``handle.project``
   for users who want the record itself. Create sets the four attributes
   below; get fills whatever the platform holds. See :ref:`projects` for how
   to read them through the handle.

   .. autoattribute:: arango_ai_sdk.models.AiProject.project_name
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.AiProject.project_type
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.AiProject.project_db_name
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.AiProject.project_description
      :no-value:

   The remaining attributes, ``project_metadata``, ``project_files`` and
   ``model_settings``, describe a project's later state. Create leaves them at
   their empty defaults; get returns them as stored.

.. py:class:: arango_ai_sdk.models.CreateProjectRequest

   Data class :meth:`~arango_ai_sdk.projects.ProjectManager.create` fills and
   sends. Not constructed by callers.

Secret profiles
---------------

.. py:class:: arango_ai_sdk.models.Profile

   A secret profile as the platform returned it. Returned by
   :meth:`~arango_ai_sdk.secret_profiles.SecretProfileManager.create` and
   :meth:`~arango_ai_sdk.secret_profiles.SecretProfileManager.get`. See
   :ref:`secret-profiles` for how to read it.

   .. autoattribute:: arango_ai_sdk.models.Profile.profile_id
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.Profile.profile_type
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.Profile.name
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.Profile.description
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.Profile.metadata
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.Profile.secret_data
      :no-value:

      Never the secret itself: the platform returns an obfuscated copy.

   .. autoattribute:: arango_ai_sdk.models.Profile.version
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.Profile.created_at
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.Profile.updated_at
      :no-value:

.. py:class:: arango_ai_sdk.models.ProfileType

   Category of a secret profile. Passed as ``profile_type`` to
   :meth:`~arango_ai_sdk.secret_profiles.SecretProfileManager.create` and read
   back from :attr:`Profile.profile_type <arango_ai_sdk.models.Profile.profile_type>`.

   ``LLM``
      A model provider key. The default at creation, and what AutoGraph expects
      for its chat and embedding models.

   ``DATABASE``, ``CLOUD_STORAGE``, ``API_KEY``, ``OAUTH``, ``SSH``, ``CUSTOM``
      Other categories the platform defines. No SDK operation needs them today.

   ``UNSPECIFIED``
      The platform's zero value. Never pass it.

.. py:class:: arango_ai_sdk.models.CreateSecretProfileRequest

   Data class
   :meth:`~arango_ai_sdk.secret_profiles.SecretProfileManager.create` fills and
   sends. Not constructed by callers. ``profile_type`` is sent as the enum name
   (for example ``"LLM"``).

Files
-----

Generated from the file service's OpenAPI description, so they carry the same
fields and descriptions the service documents. See :ref:`files` for how to
read them.

.. py:class:: arango_ai_sdk.models.RagInputUploadResponse

   One stored file version. Returned by
   :meth:`~arango_ai_sdk.files.FileManager.upload_file`. Fields: ``id``, ``name``,
   ``database``, ``scope``, ``content_type``, ``size``, ``uploaded_at``,
   ``metadata_key``, ``version``, ``safe_to_delete`` and ``custom_metadata``.
   Uploading the same name under the same scope again keeps ``id`` and raises
   ``version``.

.. py:class:: arango_ai_sdk.models.RagInputBatchItemResult

   Outcome for one file of a multi-file upload. Returned, one per file, by
   :meth:`~arango_ai_sdk.files.FileManager.upload_files` and
   :meth:`~arango_ai_sdk.files.FileManager.upload_folder`. ``status`` is
   ``"ok"`` or ``"error"``. For a stored file the fields of
   :class:`RagInputUploadResponse` are set, except ``database``; for a rejected
   file they are ``None`` and ``detail`` says why.

.. py:class:: arango_ai_sdk.models.RagInputBatchUploadResponse

   The whole reply to a multi-file upload: ``database``, ``results``,
   ``ok_count`` and ``error_count``. The SDK returns its ``results``; the class
   is exported for callers who load a reply themselves.

Services
--------

.. py:class:: arango_ai_sdk.models.ServiceInfo

   A platform service as the platform described it. Returned by
   :meth:`~arango_ai_sdk.autograph.AutoGraph.deploy` and
   :meth:`~arango_ai_sdk.autograph.AutoGraph.undeploy`. See :ref:`autograph`.

   .. autoattribute:: arango_ai_sdk.models.ServiceInfo.service_id
      :no-value:

      The platform's ID of the service. Filled after a deploy.

   .. autoattribute:: arango_ai_sdk.models.ServiceInfo.status
      :no-value:

      What the platform reported when it answered, for example that the
      install was accepted. Not a readiness signal.

   .. autoattribute:: arango_ai_sdk.models.ServiceInfo.description
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.ServiceInfo.namespace
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.ServiceInfo.db_name
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.ServiceInfo.managing_entity
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.ServiceInfo.genai_project_name
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.ServiceInfo.service_meta
      :no-value:

.. py:class:: arango_ai_sdk.models.AutoGraphService

   The AutoGraph service as recorded in a project's metadata, reachable as
   ``handle.metadata.autograph_service`` once deployed. ``autograph.service_id``
   and ``autograph.service_url`` read from it.

.. py:class:: arango_ai_sdk.models.CreateEntityRequest

   Data class :meth:`~arango_ai_sdk.autograph.AutoGraph.deploy` and
   :meth:`~arango_ai_sdk.autorag_manager.AutoRagManager.deploy` fill and
   send. Not constructed by callers.

Ingestion
---------

What the ingestion methods on :class:`~arango_ai_sdk.autograph.AutoGraph`
return. Generated from the AutoGraph service's proto, so they carry the same
fields the service documents. Every status class has a ``status`` string whose
terminal values are listed in :class:`~arango_ai_sdk.autograph.JobState`; the
methods only return once it is ``"completed"``, and raise otherwise, so a
returned status is always a finished one. The same classes reach an
``on_progress`` callback while a step is still running. See :ref:`autograph`.

.. py:class:: arango_ai_sdk.models.RagStrategizerComplexity

   What share of the clusters, ranked by complexity, the strategizer turns
   into a full knowledge graph rather than vectors. Passed as ``complexity``
   to :meth:`~arango_ai_sdk.autograph.AutoGraph.strategize` and
   :meth:`~arango_ai_sdk.autograph.AutoGraph.ingest`.

   ``very_low``
      No cluster; everything becomes vectors.

   ``low``, ``moderate``, ``high``
      A quarter, half and three quarters of the clusters, rounded over the
      ranking. ``high`` is the default.

   ``very_high``
      Every cluster.

.. py:class:: arango_ai_sdk.models.GetBuildStatusResponse

   The state of one corpus build. Returned by
   :meth:`~arango_ai_sdk.autograph.AutoGraph.corpus_build` and as ``build``
   on :class:`~arango_ai_sdk.autograph.IngestResult`. Fields:
   ``corpus_build_id``, ``status``, ``progress`` (percent), ``message``,
   ``error``, ``error_code``, ``graph_name``, ``document_count``,
   ``cluster_count``, ``documents_added``, ``documents_removed``,
   ``documents_unchanged``, ``documents_created``, ``documents_deduplicated``,
   ``dedup_groups``, ``files_written``, ``started_at`` and ``completed_at``.
   A completed build with ``error_code`` set is a partial success. See
   :ref:`autograph-corpus-build`.

.. py:class:: arango_ai_sdk.models.GetRagStrategizerJobStatusResponse

   The progress of one strategizer run. Returned by
   :meth:`~arango_ai_sdk.autograph.AutoGraph.strategize` and as
   ``strategize`` on :class:`~arango_ai_sdk.autograph.IngestResult`. Fields:
   ``status``, ``progress`` (percent, 0.0 to 100.0), ``clusters_total`` and
   ``clusters_done``. It does not say which strategy a cluster got; see
   :class:`GetRagStrategizerStrategyResponse`.

.. py:class:: arango_ai_sdk.models.GetRagStrategizerStrategyResponse

   The strategy stored for each cluster. Returned by
   :meth:`~arango_ai_sdk.autograph.AutoGraph.strategies` and as
   ``strategies`` on :class:`~arango_ai_sdk.autograph.IngestResult`. Fields:
   ``strategies``, one entry per cluster with ``cluster_id``,
   ``strategy_type``, ``rag_partition_id``, ``entity_types``,
   ``document_count`` and ``parameters``; ``total_strategies``; and
   ``strategy_type_counts``, a mapping from strategy type to how many clusters
   got it. See :ref:`autograph-strategies`.

.. py:class:: arango_ai_sdk.models.GetOrchestrationStatusResponse

   The state of one import run. Returned by
   :meth:`~arango_ai_sdk.autograph.AutoGraph.orchestrate` and as
   ``orchestration`` on :class:`~arango_ai_sdk.autograph.IngestResult`.
   ``status`` describes the whole run; ``phase`` says where a running import
   is. Further fields: ``orchestration_id``, ``message``, ``total_jobs``,
   ``completed_jobs``, ``failed_jobs``, ``running_jobs``, ``pending_jobs``,
   ``skipped_jobs``, ``jobs`` (one entry per partition with
   ``rag_partition_id``, ``strategy_type``, ``status``, ``category``,
   ``retry_count``, ``error_message``, ``entities_added`` and ``imported``),
   ``entities_added``, ``elapsed_seconds``, ``seconds_since_progress``,
   ``output_verified`` and ``unverified_partitions``. See
   :ref:`autograph-orchestrate`.

.. py:class:: arango_ai_sdk.models.CreateCorpusBuildRequest

   Data class :meth:`~arango_ai_sdk.autograph.AutoGraph.corpus_build` fills
   and sends, with a :class:`BuildStrategy` when ``top_k`` or
   ``cluster_threshold`` is given. Not constructed by callers.

.. py:class:: arango_ai_sdk.models.BuildStrategy

   The tunable parameters of a corpus build, ``top_k`` and
   ``cluster_threshold``. Filled by
   :meth:`~arango_ai_sdk.autograph.AutoGraph.corpus_build`. Not constructed
   by callers.

.. py:class:: arango_ai_sdk.models.TriggerRagStrategizerRequest

   Data class :meth:`~arango_ai_sdk.autograph.AutoGraph.strategize` fills and
   sends. Not constructed by callers.

.. py:class:: arango_ai_sdk.models.TriggerOrchestrationRequest

   Data class :meth:`~arango_ai_sdk.autograph.AutoGraph.orchestrate` fills
   and sends; the secret profile IDs in it come from the project's model
   settings. Not constructed by callers.

Asking
------

What :meth:`~arango_ai_sdk.autorag.AutoRag.ask` sends and returns. Generated
from the retriever service's proto. See :ref:`autorag-ask`.

.. py:class:: arango_ai_sdk.models.QueryType

   How a retriever searches. Passed as ``query_type`` to
   :meth:`~arango_ai_sdk.autorag.AutoRag.ask`. The SDK default is ``UNIFIED``.

   ``LOCAL``
      The entities named in the question and their relationships.

   ``GLOBAL``
      Summaries across the graph. Needs full-graph partitions.

   ``UNIFIED``
      Matching passages and the graph together. Works on vectors-only and
      full-graph partitions.

   ``CUSTOM``
      A service-defined mode. ``ask`` can send the value; it does not take
      the custom-tool arguments that mode needs.

.. py:class:: arango_ai_sdk.models.GraphRagQueryResponse

   The answer from one question. Returned by
   :meth:`~arango_ai_sdk.autorag.AutoRag.ask`. Fields: ``result`` (the answer
   text), ``run_id`` (the stored query run) and ``metadata`` (empty unless
   ``include_metadata=True``). A response whose ``error_code`` is set is not
   returned; ``ask`` raises
   :exc:`~arango_ai_sdk.exceptions.QueryFailedError` instead.

.. py:class:: arango_ai_sdk.models.GraphRagQueryRequest

   Data class :meth:`~arango_ai_sdk.autorag.AutoRag.ask` fills and sends.
   Not constructed by callers.
