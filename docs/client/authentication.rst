.. _authentication:

Authentication
==============

You supply a username and a password once, when you construct the client. The
SDK handles everything else: you never obtain, store, attach, or renew a token
yourself.

What the SDK does with your credentials
---------------------------------------

**Signs in at construction.** Constructing
:class:`~arango_ai_sdk.ArangoAIClient` exchanges the credentials for a token
and, in the same step, checks that the database you named exists and is
accessible to that account. A wrong password or a misspelt database name
therefore fails immediately.

**Keeps the token in memory only.** The token lives inside the client for its
lifetime. It is not written to disk, not exposed through any property, and not
logged.

**Attaches it to every request.** Every call made through any namespace on the
client carries a valid token. There is no per-call authentication argument.

**Renews it when the deployment rejects it.** Tokens expire. When a request is
rejected because the token is no longer valid, the SDK signs in again with the
credentials it holds and retries the request once. This also covers a client
that sat idle past the token's lifetime: the first call after the pause simply
works. Only if the fresh token is rejected too does the failure reach you.

**Never retries a rejected login.** If the deployment rejects the username or
password, the SDK raises immediately. Repeating a rejected login cannot succeed
and, against some backends, counts towards a lockout.

Errors you can see
------------------

All of these descend from :exc:`~arango_ai_sdk.exceptions.ArangoAIError`; the
first two also descend from :exc:`~arango_ai_sdk.exceptions.AuthenticationError`.

:exc:`~arango_ai_sdk.exceptions.InvalidCredentialsError`
   The deployment rejected the username or password, at construction or at a
   later renewal.

:exc:`~arango_ai_sdk.exceptions.TokenRefreshError`
   A token was needed but the exchange failed for a reason other than wrong
   credentials.

:exc:`~arango_ai_sdk.exceptions.AuthenticationError`
   Raised as the base class when a freshly obtained token was rejected as well.

:exc:`~arango_ai_sdk.exceptions.DatabaseNotFoundError`
   The database named at construction does not exist.

:exc:`~arango_ai_sdk.exceptions.PlatformUnreachableError`
   The deployment, or its authentication endpoint, could not be reached within
   the retry budget.

Example
-------

.. code-block:: python

   from arango_ai_sdk import ArangoAIClient
   from arango_ai_sdk.exceptions import InvalidCredentialsError, PlatformUnreachableError

   try:
       client = ArangoAIClient(
           base_url="https://<your-deployment>:8529",
           username="<username>",
           password="<password>",
       )
   except InvalidCredentialsError:
       print("Check the username and password.")
   except PlatformUnreachableError:
       print("Check the endpoint and your network.")
