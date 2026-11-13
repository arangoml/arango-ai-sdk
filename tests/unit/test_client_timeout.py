"""Unit test for the request timeout setting of :class:`ArangoAIClient`; no platform needed."""

from unittest.mock import patch

from arango_ai_sdk import ArangoAIClient
from arango_ai_sdk.communication import DEFAULT_TIMEOUT


def test_timeout_reaches_the_driver_unchanged() -> None:
    """The timeout is the driver's; the client only hands it over."""
    with patch("arango_ai_sdk.communication.ArangoClient") as mock_client:
        ArangoAIClient("https://platform:8529", "user", "secret", "db", timeout=300.0)

    assert mock_client.call_args.kwargs["request_timeout"] == 300.0


def test_timeout_defaults_to_the_communication_default() -> None:
    """Leaving it out keeps the 60-second default the communication layer defines."""
    with patch("arango_ai_sdk.communication.ArangoClient") as mock_client:
        ArangoAIClient("https://platform:8529", "user", "secret", "db")

    assert mock_client.call_args.kwargs["request_timeout"] == DEFAULT_TIMEOUT
