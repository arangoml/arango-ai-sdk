Secret profiles
===============

You do not construct this class yourself. The client owns a
:class:`~arango_ai_sdk.secret_profiles.SecretProfileManager` and exposes it as
``client.secret_profile``. Its operations return
:class:`~arango_ai_sdk.models.Profile` instances, documented in :doc:`models`.

.. autoclass:: arango_ai_sdk.secret_profiles.SecretProfileManager
   :members: create, get
