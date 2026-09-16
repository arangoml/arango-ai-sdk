"""Fixtures for the unit suite; nothing here touches the platform.

The shared ``communication`` fixture in ``tests/conftest.py`` opens a real,
authenticated connection and belongs to the integration suite. Unit tests use
the placeholder below and patch ``Communication.send_request`` where a request
would be sent.
"""

import pytest

from arango_ai_sdk.communication import Communication


@pytest.fixture
def placeholder_communication() -> Communication:
    """Return a ``Communication`` instance that never connected.

    ``__new__`` skips ``__init__``, so no credentials are exchanged and no
    socket is opened. The object is a real instance of the class, so a
    ``patch("...Communication.send_request")`` applies to it.
    """
    return Communication.__new__(Communication)
