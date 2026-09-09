"""Common names used across the SDK.

One definition per name, so a rename is a single edit and a typo is an
``AttributeError`` at import time rather than a silently missing value at
runtime.
"""

__all__ = ["AcpPath", "EnvVar", "FileManagerPath", "SecretProfileKey"]


class AcpPath:
    """Gateway paths of the ACP service.

    ACP sits behind the ``/ai`` prefix on the platform gateway. The proto paths
    are relative to it, so ``post: "/v1/secrets"`` is reached at
    ``/ai/v1/secrets``.
    """

    PREFIX = "/ai/v1"
    PROJECT = f"{PREFIX}/project"
    ALL_PROJECT_NAMES = f"{PREFIX}/all_project_names"
    SECRETS = f"{PREFIX}/secrets"


class FileManagerPath:
    """Gateway paths of the file service.

    Unlike ACP, its endpoints are scoped to a database, so the paths are built
    from the database name rather than being constants.
    """

    PREFIX = "/_platform/filemanager/_db"

    @staticmethod
    def rag_input(database: str) -> str:
        """Return the upload and listing endpoint for one database."""
        return f"{FileManagerPath.PREFIX}/{database}/rag-input"

    @staticmethod
    def rag_input_batch(database: str) -> str:
        """Return the batch upload endpoint for one database."""
        return f"{FileManagerPath.rag_input(database)}/batch"


class SecretProfileKey:
    """Map keys the ACP uses inside a secret profile.

    Both are hard-coded in ACP (``gen_ai/routes/secrets_handler.py``), not part
    of the proto contract, so the SDK has to hard-code the same strings to read
    what the service returns.
    TODO: If ACP ever changes these, the SDK will break. Consider making them part
    of the proto contract instead, so the SDK can read them from the service rather
    than hard-coding them.
    """

    # ACP stores the single secret string under this key in ``Profile.secret_data``.
    SECRET_DATA = "__secret_key__"

    # ACP keeps the API's top-level ``provider`` under this key in ``Profile.metadata``.
    PROVIDER_METADATA = "_provider"


class EnvVar:
    """Environment variables the SDK and its test suite read.

    Values are the variable *names*, not their contents. Never holds a secret.
    """

    # Full platform endpoint, port included, exactly as the deployment
    # publishes it -- e.g. "https://deployment.<cluster>.svc:8529".
    # This env var is set automatically in any deployment, so it will
    # be ready to use in the integration tests on CI.
    ARANGO_DEPLOYMENT_ENDPOINT = "ARANGO_DEPLOYMENT_ENDPOINT"

    # Test-only. Account used by the integration tests. When unset, those tests
    # skip rather than fail.
    ARANGO_SDK_TEST_USERNAME = "ARANGO_SDK_TEST_USERNAME"

    # Test-only. Database that account is allowed to use.
    ARANGO_SDK_TEST_DB = "ARANGO_SDK_TEST_DB"

    # Test-only. Password for that account.
    ARANGO_SDK_TEST_PASSWORD = "ARANGO_SDK_TEST_PASSWORD"
