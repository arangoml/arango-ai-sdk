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
           |-- InvalidFileScopeError
           |-- InvalidFileMetadataError
           |-- EmptyFileError
           |-- FileBatchTooLargeError
           |-- FileUploadFailedError
           |-- InvalidServiceParametersError
           |-- ServiceNotFoundError
           |-- ServiceNotDeletableError
           |-- AutoGraphAlreadyDeployedError
           |-- AutoGraphNotDeployedError
           |-- ModelConfigNotReadyError
           |-- AutoGraphBusyError
           |-- NoStrategiesError
           |-- CategoryAlreadyBuiltError
           |-- IngestionFailedError
           |-- JobStatusLostError
           `-- JobTimeoutError

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

:exc:`~arango_ai_sdk.exceptions.InvalidFileScopeError`
   A file scope breaks the platform's rules. Normally raised before anything is
   sent, since the SDK applies the platform's rules first. See :ref:`files`.

:exc:`~arango_ai_sdk.exceptions.InvalidFileMetadataError`
   The platform rejected the metadata attached to an upload. See :ref:`files`.

:exc:`~arango_ai_sdk.exceptions.EmptyFileError`
   The file to upload has no content. Normally raised before anything is sent.
   See :ref:`files`.

:exc:`~arango_ai_sdk.exceptions.FileBatchTooLargeError`
   A multi-file upload exceeds what one request may carry. Normally raised
   before anything is sent. See :ref:`files`.

:exc:`~arango_ai_sdk.exceptions.FileUploadFailedError`
   The platform could not store a file and reports having rolled the upload
   back. See :ref:`files`.

Two local problems are reported with Python's own exceptions rather than the
SDK's, because nothing was sent and the platform played no part:
:exc:`FileNotFoundError`, :exc:`IsADirectoryError` and :exc:`NotADirectoryError`
for a wrong path, and :exc:`ValueError` for a multi-file upload given no files.

:exc:`~arango_ai_sdk.exceptions.InvalidServiceParametersError`
   The platform rejected a service install parameter. See
   :ref:`autograph-deploy`.

:exc:`~arango_ai_sdk.exceptions.ServiceNotFoundError`
   The platform has no service with the ID it was asked to remove. See
   :ref:`autograph-undeploy`.

:exc:`~arango_ai_sdk.exceptions.ServiceNotDeletableError`
   The platform will not remove a service that another entity manages. See
   :ref:`autograph-undeploy`.

:exc:`~arango_ai_sdk.exceptions.AutoGraphAlreadyDeployedError`
   The project already has an AutoGraph service; a project has exactly one.
   Raised before anything is sent. See :ref:`autograph-deploy`.

:exc:`~arango_ai_sdk.exceptions.AutoGraphNotDeployedError`
   The project has no AutoGraph service to act on. Raised before anything is
   sent, by ``undeploy`` and by every ingestion method. See
   :ref:`autograph-undeploy`.

:exc:`~arango_ai_sdk.exceptions.ModelConfigNotReadyError`
   AutoGraph refused to start a job because it cannot use its chat or
   embedding settings: a startup check found them invalid, or it is still
   loading them. Fix the settings or retry shortly. See
   :ref:`autograph-corpus-build`.

:exc:`~arango_ai_sdk.exceptions.AutoGraphBusyError`
   AutoGraph refused to start a job because another build, strategizer run,
   import or delete is in progress for the project. Wait for it and retry.
   See :ref:`autograph`.

:exc:`~arango_ai_sdk.exceptions.NoStrategiesError`
   The import was asked to run on categories that have no stored strategy.
   Run the strategizer first. See :ref:`autograph-orchestrate`.

:exc:`~arango_ai_sdk.exceptions.CategoryAlreadyBuiltError`
   The corpus build was asked to build a category that is already built, and
   ``incremental`` was ``False``. See :ref:`autograph-corpus-build`.

:exc:`~arango_ai_sdk.exceptions.IngestionFailedError`
   An ingestion step ended as failed or cancelled. ``job_status`` on the
   exception is the last status the platform returned for it. See
   :ref:`autograph-waiting`.

:exc:`~arango_ai_sdk.exceptions.JobStatusLostError`
   The platform no longer has a status for the step being waited on, usually
   because the service restarted. ``job_id`` on the exception names it; the
   step itself may still be running. See :ref:`autograph-waiting`.

:exc:`~arango_ai_sdk.exceptions.JobTimeoutError`
   The ``timeout`` passed to an ingestion method ran out before the step
   finished. The step keeps running on the platform. See
   :ref:`autograph-waiting`.

The full reference is in :doc:`/api/exceptions`.
