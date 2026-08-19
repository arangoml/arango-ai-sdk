from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_documents_request import UpdateDocumentsRequest
from ...models.update_documents_response import UpdateDocumentsResponse
from ...types import Response


def _get_kwargs(
    *,
    body: UpdateDocumentsRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/graph/update",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[UpdateDocumentsResponse]:
    if response.status_code == 200:
        response_200 = UpdateDocumentsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[UpdateDocumentsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateDocumentsRequest,
) -> Response[UpdateDocumentsResponse]:
    """UpdateDocuments replaces a batch of documents (delete leg then insert leg)
     under a single mutation slot. Returns immediately; the delete+insert runs
     in the background and progress is surfaced via the importerOrchestration
     status slot.

    Args:
        body (UpdateDocumentsRequest): UpdateDocumentsRequest contains a batch of files to replace
            in an existing
             corpus graph. Files are referenced by File Manager id, exactly as
             InsertDocumentsRequest does: the replacement content is always read back from
             the File Manager, never sent inline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[UpdateDocumentsResponse]
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
    body: UpdateDocumentsRequest,
) -> Optional[UpdateDocumentsResponse]:
    """UpdateDocuments replaces a batch of documents (delete leg then insert leg)
     under a single mutation slot. Returns immediately; the delete+insert runs
     in the background and progress is surfaced via the importerOrchestration
     status slot.

    Args:
        body (UpdateDocumentsRequest): UpdateDocumentsRequest contains a batch of files to replace
            in an existing
             corpus graph. Files are referenced by File Manager id, exactly as
             InsertDocumentsRequest does: the replacement content is always read back from
             the File Manager, never sent inline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        UpdateDocumentsResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateDocumentsRequest,
) -> Response[UpdateDocumentsResponse]:
    """UpdateDocuments replaces a batch of documents (delete leg then insert leg)
     under a single mutation slot. Returns immediately; the delete+insert runs
     in the background and progress is surfaced via the importerOrchestration
     status slot.

    Args:
        body (UpdateDocumentsRequest): UpdateDocumentsRequest contains a batch of files to replace
            in an existing
             corpus graph. Files are referenced by File Manager id, exactly as
             InsertDocumentsRequest does: the replacement content is always read back from
             the File Manager, never sent inline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[UpdateDocumentsResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateDocumentsRequest,
) -> Optional[UpdateDocumentsResponse]:
    """UpdateDocuments replaces a batch of documents (delete leg then insert leg)
     under a single mutation slot. Returns immediately; the delete+insert runs
     in the background and progress is surfaced via the importerOrchestration
     status slot.

    Args:
        body (UpdateDocumentsRequest): UpdateDocumentsRequest contains a batch of files to replace
            in an existing
             corpus graph. Files are referenced by File Manager id, exactly as
             InsertDocumentsRequest does: the replacement content is always read back from
             the File Manager, never sent inline.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        UpdateDocumentsResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
