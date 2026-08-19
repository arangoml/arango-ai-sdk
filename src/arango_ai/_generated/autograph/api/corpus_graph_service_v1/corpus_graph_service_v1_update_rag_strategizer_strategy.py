from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_rag_strategizer_strategy_request import UpdateRagStrategizerStrategyRequest
from ...models.update_rag_strategizer_strategy_response import UpdateRagStrategizerStrategyResponse
from ...types import Response


def _get_kwargs(
    cluster_id: str,
    *,
    body: UpdateRagStrategizerStrategyRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v1/rag-strategizer/strategy/{cluster_id}".format(
            cluster_id=cluster_id,
        ),
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[UpdateRagStrategizerStrategyResponse]:
    if response.status_code == 200:
        response_200 = UpdateRagStrategizerStrategyResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[UpdateRagStrategizerStrategyResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    cluster_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateRagStrategizerStrategyRequest,
) -> Response[UpdateRagStrategizerStrategyResponse]:
    """UpdateRagStrategizerStrategy edits and persists the strategy for a specific cluster.
     Returns 409 if orchestration is running.

    Args:
        cluster_id (str):
        body (UpdateRagStrategizerStrategyRequest): UpdateRagStrategizerStrategyRequest contains
            the fields to override for a cluster strategy.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[UpdateRagStrategizerStrategyResponse]
    """

    kwargs = _get_kwargs(
        cluster_id=cluster_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    cluster_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateRagStrategizerStrategyRequest,
) -> Optional[UpdateRagStrategizerStrategyResponse]:
    """UpdateRagStrategizerStrategy edits and persists the strategy for a specific cluster.
     Returns 409 if orchestration is running.

    Args:
        cluster_id (str):
        body (UpdateRagStrategizerStrategyRequest): UpdateRagStrategizerStrategyRequest contains
            the fields to override for a cluster strategy.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        UpdateRagStrategizerStrategyResponse
    """

    return sync_detailed(
        cluster_id=cluster_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    cluster_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateRagStrategizerStrategyRequest,
) -> Response[UpdateRagStrategizerStrategyResponse]:
    """UpdateRagStrategizerStrategy edits and persists the strategy for a specific cluster.
     Returns 409 if orchestration is running.

    Args:
        cluster_id (str):
        body (UpdateRagStrategizerStrategyRequest): UpdateRagStrategizerStrategyRequest contains
            the fields to override for a cluster strategy.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[UpdateRagStrategizerStrategyResponse]
    """

    kwargs = _get_kwargs(
        cluster_id=cluster_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    cluster_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateRagStrategizerStrategyRequest,
) -> Optional[UpdateRagStrategizerStrategyResponse]:
    """UpdateRagStrategizerStrategy edits and persists the strategy for a specific cluster.
     Returns 409 if orchestration is running.

    Args:
        cluster_id (str):
        body (UpdateRagStrategizerStrategyRequest): UpdateRagStrategizerStrategyRequest contains
            the fields to override for a cluster strategy.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        UpdateRagStrategizerStrategyResponse
    """

    return (
        await asyncio_detailed(
            cluster_id=cluster_id,
            client=client,
            body=body,
        )
    ).parsed
