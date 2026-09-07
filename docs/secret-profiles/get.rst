.. _secret-profiles-get:

Getting a secret profile
========================

.. code-block:: python

   profile = client.secret_profile.get(profile_id)

Fetches an existing profile by the ID that
:ref:`create <secret-profiles-create>` returned, or that you copied from the
platform UI.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 22 18 60

   * - Parameter
     - Type
     - Meaning
   * - ``profile_id``
     - ``str``
     - The profile's ID.

Return value
------------

A :class:`~arango_ai_sdk.models.Profile`. See :ref:`secret-profiles` for the
attribute descriptions. As with create, ``secret_data`` is an obfuscated copy;
the secret itself cannot be read back.

Errors
------

:exc:`~arango_ai_sdk.exceptions.SecretProfileNotFoundError`
   No profile with this ID exists, or ``profile_id`` is empty.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import SecretProfileNotFoundError

   try:
       profile = client.secret_profile.get("does-not-exist")
   except SecretProfileNotFoundError:
       print("Create the profile first.")
   else:
       print(profile.name, profile.profile_type)
