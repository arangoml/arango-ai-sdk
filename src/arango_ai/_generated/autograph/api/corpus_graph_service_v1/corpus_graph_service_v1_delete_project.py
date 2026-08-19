from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_project_response import DeleteProjectResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project: str,
    *,
    delete_files: Union[Unset, bool] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["deleteFiles"] = delete_files

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v1/projects/{project}".format(
            project=project,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DeleteProjectResponse]:
    if response.status_code == 200:
        response_200 = DeleteProjectResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DeleteProjectResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project: str,
    *,
    client: Union[AuthenticatedClient, Client],
    delete_files: Union[Unset, bool] = UNSET,
) -> Response[DeleteProjectResponse]:
    r"""DeleteProject synchronously removes all AutoGraph-owned artifacts for a
     project. The running AutoGraph service is torn down only after the success
     response has been sent to the caller.
     delete_files is intentionally a query parameter (?delete_files=true). Do NOT
     add `body: \"*\"` here: DELETE bodies are frequently stripped by clients and
     proxies, and a body binding would silently drop the deliberate file-wipe
     opt-in. See DeleteProjectRequest.delete_files.

    Args:
        project (str):
        delete_files (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteProjectResponse]
    """

    kwargs = _get_kwargs(
        project=project,
        delete_files=delete_files,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project: str,
    *,
    client: Union[AuthenticatedClient, Client],
    delete_files: Union[Unset, bool] = UNSET,
) -> Optional[DeleteProjectResponse]:
    r"""DeleteProject synchronously removes all AutoGraph-owned artifacts for a
     project. The running AutoGraph service is torn down only after the success
     response has been sent to the caller.
     delete_files is intentionally a query parameter (?delete_files=true). Do NOT
     add `body: \"*\"` here: DELETE bodies are frequently stripped by clients and
     proxies, and a body binding would silently drop the deliberate file-wipe
     opt-in. See DeleteProjectRequest.delete_files.

    Args:
        project (str):
        delete_files (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteProjectResponse
    """

    return sync_detailed(
        project=project,
        client=client,
        delete_files=delete_files,
    ).parsed


async def asyncio_detailed(
    project: str,
    *,
    client: Union[AuthenticatedClient, Client],
    delete_files: Union[Unset, bool] = UNSET,
) -> Response[DeleteProjectResponse]:
    r"""DeleteProject synchronously removes all AutoGraph-owned artifacts for a
     project. The running AutoGraph service is torn down only after the success
     response has been sent to the caller.
     delete_files is intentionally a query parameter (?delete_files=true). Do NOT
     add `body: \"*\"` here: DELETE bodies are frequently stripped by clients and
     proxies, and a body binding would silently drop the deliberate file-wipe
     opt-in. See DeleteProjectRequest.delete_files.

    Args:
        project (str):
        delete_files (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteProjectResponse]
    """

    kwargs = _get_kwargs(
        project=project,
        delete_files=delete_files,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project: str,
    *,
    client: Union[AuthenticatedClient, Client],
    delete_files: Union[Unset, bool] = UNSET,
) -> Optional[DeleteProjectResponse]:
    r"""DeleteProject synchronously removes all AutoGraph-owned artifacts for a
     project. The running AutoGraph service is torn down only after the success
     response has been sent to the caller.
     delete_files is intentionally a query parameter (?delete_files=true). Do NOT
     add `body: \"*\"` here: DELETE bodies are frequently stripped by clients and
     proxies, and a body binding would silently drop the deliberate file-wipe
     opt-in. See DeleteProjectRequest.delete_files.

    Args:
        project (str):
        delete_files (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteProjectResponse
    """

    return (
        await asyncio_detailed(
            project=project,
            client=client,
            delete_files=delete_files,
        )
    ).parsed
