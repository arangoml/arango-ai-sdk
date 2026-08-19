from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.embed_field_in_collection_request import EmbedFieldInCollectionRequest
from ...models.embed_field_in_collection_response import EmbedFieldInCollectionResponse
from ...types import Response


def _get_kwargs(
    *,
    body: EmbedFieldInCollectionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/embed-field-in-collection",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[EmbedFieldInCollectionResponse]:
    if response.status_code == 200:
        response_200 = EmbedFieldInCollectionResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[EmbedFieldInCollectionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EmbedFieldInCollectionRequest,
) -> Response[EmbedFieldInCollectionResponse]:
    """EmbedFieldInCollection generates embeddings for documents in a collection that
     do not yet have the embedding field, stores them in <field>_embedding, and
     creates vector index and ArangoSearch view for that field. Single collection,
     single field per request; repeated calls are incremental.

    Args:
        body (EmbedFieldInCollectionRequest): EmbedFieldInCollectionRequest specifies the
            collection and field to embed.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmbedFieldInCollectionResponse]
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
    body: EmbedFieldInCollectionRequest,
) -> Optional[EmbedFieldInCollectionResponse]:
    """EmbedFieldInCollection generates embeddings for documents in a collection that
     do not yet have the embedding field, stores them in <field>_embedding, and
     creates vector index and ArangoSearch view for that field. Single collection,
     single field per request; repeated calls are incremental.

    Args:
        body (EmbedFieldInCollectionRequest): EmbedFieldInCollectionRequest specifies the
            collection and field to embed.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmbedFieldInCollectionResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EmbedFieldInCollectionRequest,
) -> Response[EmbedFieldInCollectionResponse]:
    """EmbedFieldInCollection generates embeddings for documents in a collection that
     do not yet have the embedding field, stores them in <field>_embedding, and
     creates vector index and ArangoSearch view for that field. Single collection,
     single field per request; repeated calls are incremental.

    Args:
        body (EmbedFieldInCollectionRequest): EmbedFieldInCollectionRequest specifies the
            collection and field to embed.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EmbedFieldInCollectionResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: EmbedFieldInCollectionRequest,
) -> Optional[EmbedFieldInCollectionResponse]:
    """EmbedFieldInCollection generates embeddings for documents in a collection that
     do not yet have the embedding field, stores them in <field>_embedding, and
     creates vector index and ArangoSearch view for that field. Single collection,
     single field per request; repeated calls are incremental.

    Args:
        body (EmbedFieldInCollectionRequest): EmbedFieldInCollectionRequest specifies the
            collection and field to embed.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EmbedFieldInCollectionResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
