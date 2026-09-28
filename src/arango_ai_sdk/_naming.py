"""Common names used across the SDK.

One definition per name, so a rename is a single edit and a typo is an
``AttributeError`` at import time rather than a silently missing value at
runtime.
"""

__all__ = [
    "AcpPath",
    "AutoGraphInstallParams",
    "AutoGraphPath",
    "EnvVar",
    "FileManagerPath",
    "SecretProfileKey",
]


class AcpPath:
    """Gateway paths of the ACP service.

    ACP sits behind the ``/_platform/acp`` prefix on the platform gateway. The
    proto paths are relative to it, so ``post: "/v1/secrets"`` is reached at
    ``/_platform/acp/v1/secrets``.
    """

    PREFIX = "/_platform/acp/v1"
    PROJECT = f"{PREFIX}/project"
    PROJECT_BY_NAME = f"{PREFIX}/project_by_name"
    ALL_PROJECT_NAMES = f"{PREFIX}/all_project_names"
    SECRETS = f"{PREFIX}/secrets"
    AUTOGRAPH = f"{PREFIX}/autograph"
    SERVICE = f"{PREFIX}/service"


class AutoGraphPath:
    """Endpoints of one project's AutoGraph service.

    Relative to the service's gateway path, ``AutoGraph.service_path``, which
    ACP records in the project metadata at install. Taken from the
    ``google.api.http`` options in ``proto/corpus_graph.proto``. Callers put
    the two together: ``f"{service_path}{AutoGraphPath.CORPUS_BUILDS}"``.
    """

    HEALTH = "v1/health"
    CORPUS_BUILDS = "v1/corpus/builds"
    STRATEGIZER_ANALYZE = "v1/rag-strategizer/analyze"
    STRATEGIZER_JOBS = "v1/rag-strategizer/jobs"
    STRATEGIZER_STRATEGY = "v1/rag-strategizer/strategy"
    ORCHESTRATE = "v1/orchestrate"


class FileManagerPath:
    """Gateway paths of the file service.

    Its endpoints are scoped to a database, which sits between the prefix and
    the resource: ``{PREFIX}/{database}/{RAG_INPUT}``. Callers put the three
    together.
    """

    PREFIX = "/_platform/filemanager/_db"
    RAG_INPUT = "rag-input"


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


class AutoGraphInstallParams:
    """Keys of the ``env`` map sent to ACP when installing AutoGraph.

    ACP forwards the map as flat Helm values to the ``arangodb-autograph``
    chart, so the names are the chart's value names
    (``autograph/charts/arangodb-autograph/values.yaml``), not part of the
    proto contract. The SDK builds the map from keyword arguments in
    ``ServiceApi.create_autograph``; callers never see these keys.
    """

    # Project the service belongs to and the database it lives in.
    GENAI_PROJECT_NAME = "genai_project_name"
    DB_NAME = "db_name"

    # Model providers: "openai", "triton" or "custom". Required by the chart.
    CHAT_API_PROVIDER = "chat_api_provider"
    EMBEDDING_API_PROVIDER = "embedding_api_provider"

    # Secret profiles holding the provider API keys.
    CHAT_SECRET_PROFILE_ID = "chat_secret_profile_id"
    EMBEDDING_SECRET_PROFILE_ID = "embedding_secret_profile_id"

    # ArangoDB user AutoGraph uses to resume File Parser work after a restart.
    # Required by the chart; the SDK does not create the user.
    FPS_RECOVERY_USERNAME = "fps_recovery_username"

    # Optional model settings. Omitted from the map when not given.
    CHAT_MODEL = "chat_model"
    EMBEDDING_MODEL = "embedding_model"
    CHAT_API_URL = "chat_api_url"
    EMBEDDING_API_URL = "embedding_api_url"
    MULTIMODAL_MODEL = "multimodal_model"


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
