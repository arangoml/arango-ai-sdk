"""Common names used across the SDK.

One definition per name, so a rename is a single edit and a typo is an
``AttributeError`` at import time rather than a silently missing value at
runtime.
"""

__all__ = ["EnvVar"]


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
