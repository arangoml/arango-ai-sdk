.. _secret-profiles-create:

Creating a secret profile
=========================

.. code-block:: python

   profile = client.secret_profile.create(
       "openai-prod",
       "sk-...",
       provider="openai",
       description="Production key for the chat model.",
   )

One call stores the secret encrypted on the platform and returns the profile.
Keep ``profile.profile_id``; that is what later stages ask for.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 22 22 56

   * - Parameter
     - Type
     - Meaning
   * - ``name``
     - ``str``
     - Human-readable name. Letters, digits, spaces, underscores and hyphens,
       1 to 63 characters.
   * - ``secret``
     - ``str``
     - The secret to store, for example an API key. Not empty, at most 4096
       characters.
   * - ``provider``
     - ``str``, optional
     - Which provider the secret belongs to, for example ``"openai"``.
       Keyword-only. Recommended, so later stages can pick the right profile.
   * - ``description``
     - ``str``, optional
     - Free text, at most 1024 characters. Keyword-only.
   * - ``profile_type``
     - :class:`~arango_ai_sdk.models.ProfileType`, optional
     - Category of the profile. Keyword-only. Defaults to ``ProfileType.LLM``,
       which is what AutoGraph expects for chat and embedding keys.

The name and the secret are validated by the platform, not by the SDK, so a
rejected value surfaces as one of the errors below rather than before the call.

Return value
------------

A :class:`~arango_ai_sdk.models.Profile`. See :ref:`secret-profiles` for the
attribute descriptions. ``secret_data`` holds an obfuscated copy of the secret,
never the secret itself.

Errors
------

:exc:`~arango_ai_sdk.exceptions.InvalidSecretNameError`
   The name was rejected: it is empty, too long, or contains characters outside
   letters, digits, spaces, underscores and hyphens.

:exc:`~arango_ai_sdk.exceptions.InvalidSecretValueError`
   The secret was rejected: it is empty, whitespace only, or longer than 4096
   characters. The message does not contain the secret.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import InvalidSecretNameError, InvalidSecretValueError

   try:
       profile = client.secret_profile.create("openai prod!", "sk-...", provider="openai")
   except InvalidSecretNameError as exc:
       print(f"Choose another name: {exc}")
   except InvalidSecretValueError as exc:
       print(f"Check the key: {exc}")
   else:
       print(f"Stored as {profile.profile_id}")
