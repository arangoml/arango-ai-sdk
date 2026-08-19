from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.trigger_rag_strategizer_request import TriggerRAGStrategizerRequest
from ...models.trigger_rag_strategizer_response import TriggerRAGStrategizerResponse
from ...types import Response


def _get_kwargs(
    *,
    body: TriggerRAGStrategizerRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/rag-strategizer/analyze",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[TriggerRAGStrategizerResponse]:
    if response.status_code == 200:
        response_200 = TriggerRAGStrategizerResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[TriggerRAGStrategizerResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: TriggerRAGStrategizerRequest,
) -> Response[TriggerRAGStrategizerResponse]:
    """TriggerRAGStrategizer analyzes existing clusters and selects optimal RAG strategy.
     This endpoint should be called AFTER a corpus build is completed.
     It analyzes document clusters using simple lexical metrics (word density and average word length)
     to recommend either VectorRAG or FullGraphRAG for each domain.

    Args:
        body (TriggerRAGStrategizerRequest): TriggerRAGStrategizerRequest contains parameters for
            RAG strategy analysis.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TriggerRAGStrategizerResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: TriggerRAGStrategizerRequest,
) -> Optional[TriggerRAGStrategizerResponse]:
    """TriggerRAGStrategizer analyzes existing clusters and selects optimal RAG strategy.
     This endpoint should be called AFTER a corpus build is completed.
     It analyzes document clusters using simple lexical metrics (word density and average word length)
     to recommend either VectorRAG or FullGraphRAG for each domain.

    Args:
        body (TriggerRAGStrategizerRequest): TriggerRAGStrategizerRequest contains parameters for
            RAG strategy analysis.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TriggerRAGStrategizerResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: TriggerRAGStrategizerRequest,
) -> Response[TriggerRAGStrategizerResponse]:
    """TriggerRAGStrategizer analyzes existing clusters and selects optimal RAG strategy.
     This endpoint should be called AFTER a corpus build is completed.
     It analyzes document clusters using simple lexical metrics (word density and average word length)
     to recommend either VectorRAG or FullGraphRAG for each domain.

    Args:
        body (TriggerRAGStrategizerRequest): TriggerRAGStrategizerRequest contains parameters for
            RAG strategy analysis.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TriggerRAGStrategizerResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: TriggerRAGStrategizerRequest,
) -> Optional[TriggerRAGStrategizerResponse]:
    """TriggerRAGStrategizer analyzes existing clusters and selects optimal RAG strategy.
     This endpoint should be called AFTER a corpus build is completed.
     It analyzes document clusters using simple lexical metrics (word density and average word length)
     to recommend either VectorRAG or FullGraphRAG for each domain.

    Args:
        body (TriggerRAGStrategizerRequest): TriggerRAGStrategizerRequest contains parameters for
            RAG strategy analysis.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TriggerRAGStrategizerResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
