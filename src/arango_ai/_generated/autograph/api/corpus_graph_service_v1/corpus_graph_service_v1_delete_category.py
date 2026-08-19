from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.delete_category_response import DeleteCategoryResponse
from ...types import Unset


def _get_kwargs(
    project: str,
    category: str,
    *,
    delete_files: Union[Unset, bool] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["deleteFiles"] = delete_files

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v1/projects/{project}/categories/{category}".format(
            project=project,
            category=category,
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[DeleteCategoryResponse]:
    if response.status_code == 200:
        response_200 = DeleteCategoryResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[DeleteCategoryResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project: str,
    category: str,
    *,
    client: Union[AuthenticatedClient, Client],
    delete_files: Union[Unset, bool] = UNSET,
) -> Response[DeleteCategoryResponse]:
    r"""DeleteCategory removes a whole category (module alias) synchronously.
     The corpus/KG contribution of the category is cleaned first
     (delete_module_data), then, when delete_files is true and the category has
     files, they are deleted via the File Manager shared library by scope + name.
     Deletion respects each file's stored safe_to_delete flag: files with
     safe_to_delete=true are removed; files with safe_to_delete=false (locked)
     are reported in locked_skipped and left intact. A category that has no files
     (\"unused\") unregisters its empty scope instead of deleting; an unknown
     category is 404. Rejected with 409 while a corpus build or orchestration is
     in progress.

    Args:
        project (str):
        category (str):
        delete_files (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteCategoryResponse]
    """

    kwargs = _get_kwargs(
        project=project,
        category=category,
        delete_files=delete_files,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project: str,
    category: str,
    *,
    client: Union[AuthenticatedClient, Client],
    delete_files: Union[Unset, bool] = UNSET,
) -> Optional[DeleteCategoryResponse]:
    r"""DeleteCategory removes a whole category (module alias) synchronously.
     The corpus/KG contribution of the category is cleaned first
     (delete_module_data), then, when delete_files is true and the category has
     files, they are deleted via the File Manager shared library by scope + name.
     Deletion respects each file's stored safe_to_delete flag: files with
     safe_to_delete=true are removed; files with safe_to_delete=false (locked)
     are reported in locked_skipped and left intact. A category that has no files
     (\"unused\") unregisters its empty scope instead of deleting; an unknown
     category is 404. Rejected with 409 while a corpus build or orchestration is
     in progress.

    Args:
        project (str):
        category (str):
        delete_files (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteCategoryResponse
    """

    return sync_detailed(
        project=project,
        category=category,
        client=client,
        delete_files=delete_files,
    ).parsed


async def asyncio_detailed(
    project: str,
    category: str,
    *,
    client: Union[AuthenticatedClient, Client],
    delete_files: Union[Unset, bool] = UNSET,
) -> Response[DeleteCategoryResponse]:
    r"""DeleteCategory removes a whole category (module alias) synchronously.
     The corpus/KG contribution of the category is cleaned first
     (delete_module_data), then, when delete_files is true and the category has
     files, they are deleted via the File Manager shared library by scope + name.
     Deletion respects each file's stored safe_to_delete flag: files with
     safe_to_delete=true are removed; files with safe_to_delete=false (locked)
     are reported in locked_skipped and left intact. A category that has no files
     (\"unused\") unregisters its empty scope instead of deleting; an unknown
     category is 404. Rejected with 409 while a corpus build or orchestration is
     in progress.

    Args:
        project (str):
        category (str):
        delete_files (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteCategoryResponse]
    """

    kwargs = _get_kwargs(
        project=project,
        category=category,
        delete_files=delete_files,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project: str,
    category: str,
    *,
    client: Union[AuthenticatedClient, Client],
    delete_files: Union[Unset, bool] = UNSET,
) -> Optional[DeleteCategoryResponse]:
    r"""DeleteCategory removes a whole category (module alias) synchronously.
     The corpus/KG contribution of the category is cleaned first
     (delete_module_data), then, when delete_files is true and the category has
     files, they are deleted via the File Manager shared library by scope + name.
     Deletion respects each file's stored safe_to_delete flag: files with
     safe_to_delete=true are removed; files with safe_to_delete=false (locked)
     are reported in locked_skipped and left intact. A category that has no files
     (\"unused\") unregisters its empty scope instead of deleting; an unknown
     category is 404. Rejected with 409 while a corpus build or orchestration is
     in progress.

    Args:
        project (str):
        category (str):
        delete_files (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteCategoryResponse
    """

    return (
        await asyncio_detailed(
            project=project,
            category=category,
            client=client,
            delete_files=delete_files,
        )
    ).parsed
