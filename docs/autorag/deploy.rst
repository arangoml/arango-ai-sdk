.. _autorag-deploy:

Deploying a retriever
=====================

.. code-block:: python

   deployed = sales.autorag.deploy(
       chat_api_provider="openai",
       embedding_api_provider="openai",
       chat_secret_profile_id=chat.profile_id,
       embedding_secret_profile_id=embed.profile_id,
       chat_model="gpt-4o",
       embedding_model="text-embedding-3-small",
   )
   retriever = deployed.autorag

One call installs a new retriever into the handle's project and returns the
service record the platform created, together with the
:class:`~arango_ai_sdk.managers.autorag.AutoRag` bound to it. The project name and
database are not parameters: they come from the handle.

You pass Python arguments, not platform install keys; the SDK builds the
install request from them. A project can hold several retrievers, so this
call does not look for one that is already there and does not refuse when it
finds one. Each call adds a retriever.

The arguments are the same model settings as :ref:`autograph-deploy`, with
two differences. There is no ``fps_recovery_username``: a retriever does not
resume File Parser work. There is no ``multimodal_model``.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 32 18 50

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
   * - ``chat_model``
     - ``str``, optional
     - Chat model name, for example ``"gpt-4o"``. A question uses this model
       unless :ref:`autorag-ask` overrides it for that one call.
   * - ``embedding_model``
     - ``str``, optional
     - Embedding model name, for example ``"text-embedding-3-small"``.
   * - ``chat_api_url``
     - ``str``, optional
     - Override for the chat provider's endpoint.
   * - ``embedding_api_url``
     - ``str``, optional
     - Override for the embedding provider's endpoint.
   * - ``labels``
     - mapping of ``str`` to ``str``, optional
     - Labels attached to the deployed service on the platform.
   * - ``wait``
     - ``bool``
     - Also wait for the health check before returning. Default ``False``.

Optional parameters are left out of the install request when not given. The
SDK does not validate the required strings; an empty value is sent as is.

Return value
------------

An :class:`~arango_ai_sdk.managers.autorag_manager.AutoRagDeployResult` with three
attributes.

``service_info`` is the :class:`~arango_ai_sdk.models.ServiceInfo` describing
the service right after the install request was accepted: its ``service_id``
is the platform's ID of the new retriever, and ``status`` is what the
platform reported at that moment. Acceptance is not readiness: the pod may
still be starting.

``autorag`` is the :class:`~arango_ai_sdk.managers.autorag.AutoRag` bound to that id.
Asking and removing go through it.

``ready`` tells whether the service answered its health check with ``OK``.
It is ``None`` when you did not pass ``wait=True``, since nobody checked.
With ``wait=True`` it is ``True`` when the service became ready within the
bound and ``False`` when the bound passed first. A slow start does not fail
the deploy and does not remove the service. Unless ``ready`` is ``True``,
call ``wait_until_ready`` yourself:

.. code-block:: python

   deployed = sales.autorag.deploy(..., wait=True)
   retriever = deployed.autorag
   if not deployed.ready and not retriever.wait_until_ready(timeout=600.0):
       raise SystemExit("The retriever did not become ready.")

The handle is reloaded after the call, so the new id shows up in
``sales.autorag.list()``.

Waiting until it is serving
---------------------------

``wait_until_ready`` blocks until the retriever answers its health check
with ``OK``.

.. list-table::
   :header-rows: 1
   :widths: 22 22 56

   * - Parameter
     - Type
     - Meaning
   * - ``timeout``
     - ``float``
     - Seconds to wait before giving up. Default 300.
   * - ``poll_interval``
     - ``float``
     - Seconds between two health checks. Default 5.

It returns ``True`` once the check answers ``OK``, and ``False`` when
``timeout`` passed first. A failed request while the route or the pod is
still coming up counts as not ready, not as an error, so a retriever that is
slow to start does not raise. The wait is only "is the process up". It is
not a limit on a question you ask afterwards.

Errors
------

:exc:`~arango_ai_sdk.exceptions.ProjectNotFoundError`
   The project no longer exists on the platform.

:exc:`~arango_ai_sdk.exceptions.InvalidServiceParametersError`
   The platform rejected one of the install parameters.

:exc:`~arango_ai_sdk.exceptions.AutoRagNotDeployedError`
   ``wait_until_ready`` reloaded the project and this retriever was no longer
   in it. Nothing was left to wait for.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`, for example :exc:`~arango_ai_sdk.exceptions.ServiceError`
carrying the status code and message the platform returned.

Example
-------

.. code-block:: python

   sales = client.project.get(project_name="sales")
   deployed = sales.autorag.deploy(
       chat_api_provider="openai",
       embedding_api_provider="openai",
       chat_secret_profile_id=chat.profile_id,
       embedding_secret_profile_id=embed.profile_id,
       chat_model="gpt-4o",
       embedding_model="text-embedding-3-small",
   )
   print(deployed.service_info.service_id, deployed.ready)
   if not deployed.autorag.wait_until_ready():
       print("Still starting; ask later or raise the timeout.")
