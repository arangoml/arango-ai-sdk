.. _secret-profiles:

Secret profiles
===============

A secret profile stores one secret, typically an API key for a model provider,
encrypted on the platform. You create it once and from then on refer to it by
its ``profile_id``. Later stages take a profile ID rather than the key itself:
AutoGraph asks for one profile for the chat model and one for the embedding
model. The key never leaves the platform again.

The secret profiles area is the ``secret_profile`` namespace on the client:

.. code-block:: python

   profile = client.secret_profile.create(name="openai-prod", secret="sk-...", provider="openai")
   print(profile.profile_id)

.. toctree::
   :maxdepth: 1

   create
   get

Available operations
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Operation
     - Status
     - Page
   * - Create a secret profile
     - Available
     - :ref:`secret-profiles-create`
   * - Get a secret profile by ID
     - Available
     - :ref:`secret-profiles-get`
   * - List, update or delete a secret profile
     - Not yet available
     - Arrives in a later release.

The returned profile
--------------------

Operations that return a profile return a
:class:`~arango_ai_sdk.models.Profile` with these attributes:

``profile_id``
   The ID later stages use to refer to the secret. This is the value to keep.

``name``
   The name you gave the profile.

``profile_type``
   A :class:`~arango_ai_sdk.models.ProfileType`. ``ProfileType.LLM`` for model
   provider keys, which is the default at creation.

``description``
   The description, or ``None`` if none was given.

``metadata``
   Non-sensitive key-value pairs the platform keeps with the profile. The
   ``provider`` you passed at creation is stored here.

``secret_data``
   Never the secret itself. The platform returns an obfuscated copy that keeps
   the first two and the last two characters and replaces the rest with dots,
   so you can recognise a key without exposing it.

``version``, ``created_at``, ``updated_at``
   Bookkeeping set by the platform.

.. note::

   The secret is sent exactly once, in the create call. It is never logged by
   the SDK and never appears in an exception message.
