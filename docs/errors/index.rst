.. _errors:

Errors
======

The SDK reports failures as named exceptions, never as HTTP status codes for you
to interpret. Nothing from an underlying library escapes; every failure is
translated into one of the SDK's own exception types before it reaches you.

The exception tree
------------------

Every exception descends from :exc:`~arango_ai_sdk.exceptions.ArangoAIError`.
The tree is deliberately shallow: a root, two families, and concrete errors
underneath.

.. code-block:: text

   ArangoAIError
   |-- AuthenticationError
   |   |-- InvalidCredentialsError
   |   `-- TokenRefreshError
   `-- CommunicationError
       |-- PlatformUnreachableError
       `-- ServiceError
           |-- DatabaseNotFoundError
           |-- InvalidProjectNameError
           |-- ProjectNotFoundError
           |-- InvalidSecretNameError
           |-- InvalidSecretValueError
           |-- SecretProfileNotFoundError
           |-- InvalidScopeError
           |-- InvalidFileMetadataError
           |-- EmptyFileError
           |-- BatchTooLargeError
           `-- FileUploadFailedError

Choosing how precisely to catch
-------------------------------

Catch at whichever level fits what you want to handle:

.. code-block:: python

   from arango_ai_sdk.exceptions import (
       ArangoAIError,
       AuthenticationError,
       InvalidCredentialsError,
   )

   try:
       ...
   except InvalidCredentialsError:
       ...  # exactly: wrong username or password
   except AuthenticationError:
       ...  # any authentication problem
   except ArangoAIError:
       ...  # anything the SDK can raise

The families
------------

:exc:`~arango_ai_sdk.exceptions.AuthenticationError`
   Problems obtaining or using a token. See :ref:`authentication`.

:exc:`~arango_ai_sdk.exceptions.CommunicationError`
   Problems reaching the deployment or reading its reply. Its two children
   separate "never got there" from "got there, and it said no":

   :exc:`~arango_ai_sdk.exceptions.PlatformUnreachableError`
      The deployment could not be reached within the retry budget, or did not
      answer within the request timeout. Nothing was rejected; nothing was
      reached.

   :exc:`~arango_ai_sdk.exceptions.ServiceError`
      A service was reached and answered with an error. Where the SDK knows
      what that error means for the call you made, it raises a more specific
      subclass, such as :exc:`~arango_ai_sdk.exceptions.InvalidProjectNameError`.
      Otherwise you get ``ServiceError`` itself.

What a ``ServiceError`` carries
-------------------------------

Every :exc:`~arango_ai_sdk.exceptions.ServiceError`, including its subclasses,
has two attributes in addition to its message:

``status_code``
   The HTTP status code the service returned, or ``None``.

``error_code``
   The service's own error number, where it sent one, or ``None``.

.. code-block:: python

   from arango_ai_sdk.exceptions import ServiceError

   try:
       ...
   except ServiceError as exc:
       print(exc.status_code, exc.error_code, exc)

Concrete errors
---------------

:exc:`~arango_ai_sdk.exceptions.InvalidCredentialsError`
   The deployment rejected the username or password. Never retried.

:exc:`~arango_ai_sdk.exceptions.TokenRefreshError`
   A token was needed but could not be obtained or renewed.

:exc:`~arango_ai_sdk.exceptions.DatabaseNotFoundError`
   The database named at client construction does not exist.

:exc:`~arango_ai_sdk.exceptions.InvalidProjectNameError`
   A project name was rejected. See :ref:`projects-create`.

:exc:`~arango_ai_sdk.exceptions.ProjectNotFoundError`
   No project with the given name exists in the client's database. See
   :ref:`projects-get`.

:exc:`~arango_ai_sdk.exceptions.InvalidSecretNameError`
   A secret profile name was rejected. See :ref:`secret-profiles-create`.

:exc:`~arango_ai_sdk.exceptions.InvalidSecretValueError`
   A secret was rejected as empty or too long. The message never contains the
   secret. See :ref:`secret-profiles-create`.

:exc:`~arango_ai_sdk.exceptions.SecretProfileNotFoundError`
   No secret profile with the given ID exists. See :ref:`secret-profiles-get`.

:exc:`~arango_ai_sdk.exceptions.InvalidScopeError`
   A file scope breaks the platform's rules. Normally raised before anything is
   sent, since the SDK applies the platform's rules first. See :ref:`files`.

:exc:`~arango_ai_sdk.exceptions.InvalidFileMetadataError`
   The platform rejected the metadata attached to an upload. See :ref:`files`.

:exc:`~arango_ai_sdk.exceptions.EmptyFileError`
   The file to upload has no content. Normally raised before anything is sent.
   See :ref:`files`.

:exc:`~arango_ai_sdk.exceptions.BatchTooLargeError`
   A multi-file upload exceeds what one request may carry. Normally raised
   before anything is sent. See :ref:`files`.

:exc:`~arango_ai_sdk.exceptions.FileUploadFailedError`
   The platform could not store a file and reports having rolled the upload
   back. See :ref:`files`.

Two local problems are reported with Python's own exceptions rather than the
SDK's, because nothing was sent and the platform played no part:
:exc:`FileNotFoundError`, :exc:`IsADirectoryError` and :exc:`NotADirectoryError`
for a wrong path, and :exc:`ValueError` for a multi-file upload given no files.

The full reference is in :doc:`/api/exceptions`.
