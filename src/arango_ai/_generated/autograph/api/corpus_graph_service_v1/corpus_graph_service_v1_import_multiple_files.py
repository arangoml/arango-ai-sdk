from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.import_multiple_files_request import ImportMultipleFilesRequest
from ...models.import_multiple_files_response import ImportMultipleFilesResponse
from ...types import Response


def _get_kwargs(
    *,
    body: ImportMultipleFilesRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/import-multiple",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ImportMultipleFilesResponse]:
    if response.status_code == 200:
        response_200 = ImportMultipleFilesResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ImportMultipleFilesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ImportMultipleFilesRequest,
) -> Response[ImportMultipleFilesResponse]:
    """ImportMultipleFiles accepts multiple files and imports them into the corpus graph.

    Args:
        body (ImportMultipleFilesRequest): ImportMultipleFilesRequest contains the files to be
            imported.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ImportMultipleFilesResponse]
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
    body: ImportMultipleFilesRequest,
) -> Optional[ImportMultipleFilesResponse]:
    """ImportMultipleFiles accepts multiple files and imports them into the corpus graph.

    Args:
        body (ImportMultipleFilesRequest): ImportMultipleFilesRequest contains the files to be
            imported.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ImportMultipleFilesResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ImportMultipleFilesRequest,
) -> Response[ImportMultipleFilesResponse]:
    """ImportMultipleFiles accepts multiple files and imports them into the corpus graph.

    Args:
        body (ImportMultipleFilesRequest): ImportMultipleFilesRequest contains the files to be
            imported.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ImportMultipleFilesResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ImportMultipleFilesRequest,
) -> Optional[ImportMultipleFilesResponse]:
    """ImportMultipleFiles accepts multiple files and imports them into the corpus graph.

    Args:
        body (ImportMultipleFilesRequest): ImportMultipleFilesRequest contains the files to be
            imported.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ImportMultipleFilesResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
