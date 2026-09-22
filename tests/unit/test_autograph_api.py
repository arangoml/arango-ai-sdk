"""Unit tests for :class:`AutoGraphApi`; no platform needed.

``Communication.send_request`` is patched, so the tests check the request
``AutoGraphApi`` sends, the model it loads the reply into, and the SDK
exception it translates an error answer into.
"""

from unittest.mock import patch

from arango_ai_sdk._autograph_api import AutoGraphApi
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.models import GetBuildStatusResponse

SEND_REQUEST = "arango_ai_sdk.communication.Communication.send_request"

SERVICE_PATH = "/autograph/c-123"


def test_get_corpus_build_status_returns_status(
    placeholder_communication: Communication,
):
    with patch(SEND_REQUEST) as mock_send:
        mock_send.return_value = {
            "corpusBuildId": "build-1",
            "status": "running",
            "progress": 40,
            "message": "Embedding documents",
        }
        api = AutoGraphApi(communication=placeholder_communication)

        status = api.get_corpus_build_status(service_path=SERVICE_PATH, build_id="build-1")

    mock_send.assert_called_once_with("get", f"{SERVICE_PATH}/v1/corpus/builds/build-1")
    assert isinstance(status, GetBuildStatusResponse)
    assert status.corpus_build_id == "build-1"
    assert status.status == "running"
    assert status.progress == 40
    assert status.message == "Embedding documents"
