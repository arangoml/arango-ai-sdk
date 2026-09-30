"""Unit test for the TLS verification setting of :class:`Communication`; no platform needed."""

from unittest.mock import patch

import pytest

from arango_ai_sdk.communication import Communication


@pytest.mark.parametrize("verify", [True, False, "/etc/ssl/certs/platform-ca.pem"])
def test_verify_reaches_the_driver_unchanged(verify: bool | str) -> None:
    """The TLS setting is the driver's; the SDK only hands it over."""
    with patch("arango_ai_sdk.communication.ArangoClient") as mock_client:
        Communication("https://platform:8529", "user", "secret", "db", verify=verify)

    assert mock_client.call_args.kwargs["verify_override"] is verify
