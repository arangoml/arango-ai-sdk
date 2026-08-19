from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response
from ... import errors

from ...models.delete_documents_request import DeleteDocumentsRequest
from ...models.delete_documents_response import DeleteDocumentsResponse


def _get_kwargs(
    *,
    body: DeleteDocumentsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/graph/delete",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DeleteDocumentsResponse]:
    if response.status_code == 200:
        response_200 = DeleteDocumentsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DeleteDocumentsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: DeleteDocumentsRequest,
) -> Response[DeleteDocumentsResponse]:
    """DeleteDocuments removes a batch of documents from the corpus graph
     (Layer 1/2) and cleans up the importer knowledge graph (Layer 3).

    Args:
        body (DeleteDocumentsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteDocumentsResponse]
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
    body: DeleteDocumentsRequest,
) -> Optional[DeleteDocumentsResponse]:
    """DeleteDocuments removes a batch of documents from the corpus graph
     (Layer 1/2) and cleans up the importer knowledge graph (Layer 3).

    Args:
        body (DeleteDocumentsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteDocumentsResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: DeleteDocumentsRequest,
) -> Response[DeleteDocumentsResponse]:
    """DeleteDocuments removes a batch of documents from the corpus graph
     (Layer 1/2) and cleans up the importer knowledge graph (Layer 3).

    Args:
        body (DeleteDocumentsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteDocumentsResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: DeleteDocumentsRequest,
) -> Optional[DeleteDocumentsResponse]:
    """DeleteDocuments removes a batch of documents from the corpus graph
     (Layer 1/2) and cleans up the importer knowledge graph (Layer 3).

    Args:
        body (DeleteDocumentsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteDocumentsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
