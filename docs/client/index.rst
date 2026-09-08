.. _client:

The client
==========

:class:`~arango_ai_sdk.ArangoAIClient` is the entry point to the SDK. You
construct it once with your credentials, and every area of the SDK is a
namespace on it: ``client.project`` and ``client.secret_profile`` today.

.. toctree::
   :maxdepth: 1

   authentication

Creating a client
-----------------

.. code-block:: python

   from arango_ai_sdk import ArangoAIClient

   client = ArangoAIClient(
       base_url="https://<your-deployment>:8529",
       project_name="my_project",
       username="<username>",
       password="<password>",
       db_name="_system",   # optional, this is the default
   )

``base_url``
   The full endpoint of your deployment, port included, exactly as the
   deployment publishes it.

``project_name``
   The project this client works in. It is set once, here, so no later method
   takes a project argument.

``username``, ``password``
   The account to authenticate with. The password is held in memory for the
   client's lifetime because token renewal needs it. It is never exposed again;
   there is deliberately no ``password`` property.

``db_name``
   The database to connect to. Defaults to ``_system``.

One client, one project, one database
-------------------------------------

A client is bound to the project and the database you name at construction.
That keeps every later call short: nothing asks you which project or database
you mean. To work with a second project, create a second client.

Reading back the configuration
------------------------------

The client exposes what it was constructed with as read-only properties:
``base_url``, ``project_name``, ``username`` and ``db_name``. The password is
not readable.

Closing the client
------------------

.. code-block:: python

   client.close()

``close()`` releases the HTTP sessions and sockets the client keeps open. Call it
when you are done, typically in a ``finally`` block. Calling it more than once is
safe.

What can fail at construction
-----------------------------

Signing in happens inside the constructor, so these problems surface
immediately rather than on your first real call:

:exc:`~arango_ai_sdk.exceptions.InvalidCredentialsError`
   The deployment rejected the username or password, or the account cannot
   access the database.

:exc:`~arango_ai_sdk.exceptions.DatabaseNotFoundError`
   ``db_name`` does not exist on the deployment.

:exc:`~arango_ai_sdk.exceptions.PlatformUnreachableError`
   The deployment could not be reached within the retry budget.

See :ref:`errors` for the complete list.
