"""Smoke tests: the package imports and reports a version."""

import arango_ai_sdk


def test_package_imports():
    assert arango_ai_sdk.ArangoAIClient is not None
    assert arango_ai_sdk.AiProjectHandle is not None


def test_version_is_a_non_empty_string():
    assert isinstance(arango_ai_sdk.__version__, str)
    assert arango_ai_sdk.__version__
