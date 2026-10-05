.. _autograph-deploy:

Deploying AutoGraph
===================

.. code-block:: python

   info = sales.autograph.deploy(
       chat_api_provider="openai",
       embedding_api_provider="openai",
       chat_secret_profile_id=chat.profile_id,
       embedding_secret_profile_id=embed.profile_id,
       fps_recovery_username="fps-recovery",
       chat_model="gpt-4o",
       embedding_model="text-embedding-3-small",
   )

One call installs AutoGraph into the handle's project and returns the service
record the platform created. The project name and database are not parameters:
they come from the handle. Before sending anything, ``deploy`` reloads the
project and refuses if it already has an AutoGraph service.

You pass Python arguments, not platform install keys; the SDK builds the
install request from them.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 28 18 54

   * - Parameter
     - Type
     - Meaning
   * - ``chat_api_provider``
     - ``str``
     - Provider of the chat model, for example ``"openai"``.
   * - ``embedding_api_provider``
     - ``str``
     - Provider of the embedding model, for example ``"openai"``.
   * - ``chat_secret_profile_id``
     - ``str``
     - ID of the secret profile holding the chat provider's API key. See
       :ref:`secret-profiles-create`.
   * - ``embedding_secret_profile_id``
     - ``str``
     - ID of the secret profile holding the embedding provider's API key.
   * - ``fps_recovery_username``
     - ``str``
     - ArangoDB user AutoGraph uses to resume File Parser work after a pod
       restart. Must have read and write access to the project database. The
       SDK does not create this user.
   * - ``chat_model``
     - ``str``, optional
     - Chat model name, for example ``"gpt-4o"``. Optional for the install.
       Required, together with ``embedding_model``, for a first ingestion.
   * - ``embedding_model``
     - ``str``, optional
     - Embedding model name, for example ``"text-embedding-3-small"``.
       Same rule as ``chat_model``.
   * - ``chat_api_url``
     - ``str``, optional
     - Override for the chat provider's endpoint.
   * - ``embedding_api_url``
     - ``str``, optional
     - Override for the embedding provider's endpoint.
   * - ``multimodal_model``
     - ``str``, optional
     - Multimodal model name, when documents contain images.
   * - ``labels``
     - mapping of ``str`` to ``str``, optional
     - Labels attached to the deployed service on the platform.

Optional parameters are left out of the install request when not given. The
SDK does not validate the required strings; an empty value is sent as is.

Return value
------------

A :class:`~arango_ai_sdk.autograph.DeployResult` with two attributes.
``service_info`` is the :class:`~arango_ai_sdk.models.ServiceInfo` describing
the service right after the install request was accepted: its ``service_id``
is the platform's ID of the new service, and ``status`` is what the platform
reported at that moment. Acceptance is not readiness: the pod may still be
starting.

``ready`` tells whether the service answered its health check. It is ``None``
when you did not pass ``wait=True``, since nobody checked. With ``wait=True``
it is ``True`` when the service became ready within the bound and ``False``
when the bound passed first. Unless it is ``True``, the service is still
installed and may be coming up, and ``sales.autograph.wait_until_ready()``
checks again:

.. code-block:: python

   result = sales.autograph.deploy(..., wait=True)
   if not result.ready:
       ready = sales.autograph.wait_until_ready(timeout=600.0)

The handle is reloaded after the call, so ``sales.autograph.is_deployed`` is
``True``. When the install includes both model names and both profile IDs,
the platform stores them as the project's model settings. Otherwise it keeps
whatever an earlier deploy stored, or nothing on a project's first deploy.
The settings survive undeploy, so a redeploy without model names reuses the
previous ones, including their secret profile IDs. A first deploy that
stores nothing makes :ref:`autograph-orchestrate` raise
:exc:`~arango_ai_sdk.exceptions.ServiceError` before it sends anything.

Errors
------

:exc:`~arango_ai_sdk.exceptions.AutoGraphAlreadyDeployedError`
   The project already has an AutoGraph service. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.ProjectNotFoundError`
   The project no longer exists on the platform.

:exc:`~arango_ai_sdk.exceptions.InvalidServiceParametersError`
   The platform rejected one of the install parameters.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`, for example :exc:`~arango_ai_sdk.exceptions.ServiceError`
carrying the status code and message the platform returned.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import AutoGraphAlreadyDeployedError

   sales = client.project.get(project_name="sales")
   try:
       info = sales.autograph.deploy(
           chat_api_provider="openai",
           embedding_api_provider="openai",
           chat_secret_profile_id=chat.profile_id,
           embedding_secret_profile_id=embed.profile_id,
           fps_recovery_username="fps-recovery",
       )
   except AutoGraphAlreadyDeployedError:
       print(f"Already running as {sales.autograph.service_id}")
   else:
       print(f"Deploying {info.service_info.service_id}: {info.service_info.status}")
