from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cancel_orchestration_response import CancelOrchestrationResponse
from ...types import UNSET, Response


def _get_kwargs(
    orchestration_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v1/orchestrate/{orchestration_id}".format(
            orchestration_id=orchestration_id,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[CancelOrchestrationResponse]:
    if response.status_code == 200:
        response_200 = CancelOrchestrationResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[CancelOrchestrationResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    orchestration_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[CancelOrchestrationResponse]:
    """CancelOrchestration asks the running orchestration to stop and release the
     single-flight slot, so an operator can clear a wedged run without database
     surgery (AIS-1809). Cancellation is cooperative: the run terminalises at its
     next consumption-loop pass, tears down its own importer service, and frees
     the slot -- bounded by one importer HTTP timeout, so allow up to ~2 minutes.
     A run still holding the slot ORCHESTRATION_CANCEL_GRACE_SECONDS after the
     request is force-released by the admission reaper instead.
     Returns 404 when orchestration_id is not the run currently holding the slot
     (already terminal, unknown, or evicted).

    Args:
        orchestration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CancelOrchestrationResponse]
    """

    kwargs = _get_kwargs(
        orchestration_id=orchestration_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    orchestration_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[CancelOrchestrationResponse]:
    """CancelOrchestration asks the running orchestration to stop and release the
     single-flight slot, so an operator can clear a wedged run without database
     surgery (AIS-1809). Cancellation is cooperative: the run terminalises at its
     next consumption-loop pass, tears down its own importer service, and frees
     the slot -- bounded by one importer HTTP timeout, so allow up to ~2 minutes.
     A run still holding the slot ORCHESTRATION_CANCEL_GRACE_SECONDS after the
     request is force-released by the admission reaper instead.
     Returns 404 when orchestration_id is not the run currently holding the slot
     (already terminal, unknown, or evicted).

    Args:
        orchestration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CancelOrchestrationResponse
    """

    return sync_detailed(
        orchestration_id=orchestration_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    orchestration_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[CancelOrchestrationResponse]:
    """CancelOrchestration asks the running orchestration to stop and release the
     single-flight slot, so an operator can clear a wedged run without database
     surgery (AIS-1809). Cancellation is cooperative: the run terminalises at its
     next consumption-loop pass, tears down its own importer service, and frees
     the slot -- bounded by one importer HTTP timeout, so allow up to ~2 minutes.
     A run still holding the slot ORCHESTRATION_CANCEL_GRACE_SECONDS after the
     request is force-released by the admission reaper instead.
     Returns 404 when orchestration_id is not the run currently holding the slot
     (already terminal, unknown, or evicted).

    Args:
        orchestration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CancelOrchestrationResponse]
    """

    kwargs = _get_kwargs(
        orchestration_id=orchestration_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    orchestration_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[CancelOrchestrationResponse]:
    """CancelOrchestration asks the running orchestration to stop and release the
     single-flight slot, so an operator can clear a wedged run without database
     surgery (AIS-1809). Cancellation is cooperative: the run terminalises at its
     next consumption-loop pass, tears down its own importer service, and frees
     the slot -- bounded by one importer HTTP timeout, so allow up to ~2 minutes.
     A run still holding the slot ORCHESTRATION_CANCEL_GRACE_SECONDS after the
     request is force-released by the admission reaper instead.
     Returns 404 when orchestration_id is not the run currently holding the slot
     (already terminal, unknown, or evicted).

    Args:
        orchestration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CancelOrchestrationResponse
    """

    return (
        await asyncio_detailed(
            orchestration_id=orchestration_id,
            client=client,
        )
    ).parsed
