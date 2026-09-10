Models
======

.. automodule:: arango_ai_sdk.models

The classes below are the ones the SDK returns or accepts. Import them from
``arango_ai_sdk.models``; that path stays stable even if the classes' origin
changes.

.. code-block:: python

   from arango_ai_sdk.models import AiProject, Profile, ProfileType

You construct none of these yourself. ``AiProject`` and ``Profile`` come back
from client calls. ``CreateProjectRequest`` and ``CreateSecretProfileRequest``
are data classes those calls fill; you still pass arguments on
``create``, not those objects.

``create`` fills a request data class and sends ``to_dict()``. Field names come
from the proto, so a rename fails at import time, not on the wire. ``to_dict``
emits camelCase keys, which the gateway accepts. A plain string at its zero
value is omitted; the server reads a missing field as empty, so an empty name
is still rejected. Optional fields (``project_description``, ``description``,
``provider``) track presence: ``None`` is omitted, ``""`` is sent as ``""``.

Projects
--------

.. py:class:: arango_ai_sdk.models.AiProject

   A project as the platform returned it. Returned by
   :meth:`~arango_ai_sdk.projects.ProjectManager.create`, which sets the four
   attributes below. See :ref:`projects` for how to read them.

   .. autoattribute:: arango_ai_sdk.models.AiProject.project_name
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.AiProject.project_type
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.AiProject.project_db_name
      :no-value:
   .. autoattribute:: arango_ai_sdk.models.AiProject.project_description
      :no-value:

   The remaining attributes, ``project_metadata``, ``project_files`` and
   ``model_settings``, describe a project's later state and are left at their
   empty defaults by create.

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
