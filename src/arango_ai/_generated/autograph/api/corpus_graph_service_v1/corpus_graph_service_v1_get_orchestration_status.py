from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response
from ... import errors

from ...models.get_orchestration_status_response import GetOrchestrationStatusResponse


def _get_kwargs(
    orchestration_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/orchestrate/{orchestration_id}".format(
            orchestration_id=orchestration_id,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetOrchestrationStatusResponse]:
    if response.status_code == 200:
        response_200 = GetOrchestrationStatusResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetOrchestrationStatusResponse]:
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
) -> Response[GetOrchestrationStatusResponse]:
    r"""GetOrchestrationStatus returns the current status of an orchestration run,
     including per-job details and importer failure messages.
     Poll this endpoint after POST /v1/orchestrate to track progress.
     Status lifecycle: \"running\" → \"completed\" | \"failed\" | \"cancelled\"
     Returns 404 if the orchestration_id is unknown, invalid, or has been evicted

    Args:
        orchestration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetOrchestrationStatusResponse]
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
) -> Optional[GetOrchestrationStatusResponse]:
    r"""GetOrchestrationStatus returns the current status of an orchestration run,
     including per-job details and importer failure messages.
     Poll this endpoint after POST /v1/orchestrate to track progress.
     Status lifecycle: \"running\" → \"completed\" | \"failed\" | \"cancelled\"
     Returns 404 if the orchestration_id is unknown, invalid, or has been evicted

    Args:
        orchestration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetOrchestrationStatusResponse
    """

    return sync_detailed(
        orchestration_id=orchestration_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    orchestration_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetOrchestrationStatusResponse]:
    r"""GetOrchestrationStatus returns the current status of an orchestration run,
     including per-job details and importer failure messages.
     Poll this endpoint after POST /v1/orchestrate to track progress.
     Status lifecycle: \"running\" → \"completed\" | \"failed\" | \"cancelled\"
     Returns 404 if the orchestration_id is unknown, invalid, or has been evicted

    Args:
        orchestration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetOrchestrationStatusResponse]
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
) -> Optional[GetOrchestrationStatusResponse]:
    r"""GetOrchestrationStatus returns the current status of an orchestration run,
     including per-job details and importer failure messages.
     Poll this endpoint after POST /v1/orchestrate to track progress.
     Status lifecycle: \"running\" → \"completed\" | \"failed\" | \"cancelled\"
     Returns 404 if the orchestration_id is unknown, invalid, or has been evicted

    Args:
        orchestration_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetOrchestrationStatusResponse
    """

    return (
        await asyncio_detailed(
            orchestration_id=orchestration_id,
            client=client,
        )
    ).parsed
