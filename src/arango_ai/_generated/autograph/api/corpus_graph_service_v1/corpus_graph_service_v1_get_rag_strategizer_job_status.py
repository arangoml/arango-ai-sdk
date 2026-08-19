from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_rag_strategizer_job_status_response import GetRagStrategizerJobStatusResponse
from ...types import Response


def _get_kwargs(
    strategize_job_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/rag-strategizer/jobs/{strategize_job_id}".format(
            strategize_job_id=strategize_job_id,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetRagStrategizerJobStatusResponse]:
    if response.status_code == 200:
        response_200 = GetRagStrategizerJobStatusResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetRagStrategizerJobStatusResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    strategize_job_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetRagStrategizerJobStatusResponse]:
    """GetRagStrategizerJobStatus retrieves live progress of a RAG strategizer
     analyze run by its job id. Use this endpoint to drive a UI progress bar
     while POST /v1/rag-strategizer/analyze runs in the background.

    Args:
        strategize_job_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetRagStrategizerJobStatusResponse]
    """

    kwargs = _get_kwargs(
        strategize_job_id=strategize_job_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    strategize_job_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetRagStrategizerJobStatusResponse]:
    """GetRagStrategizerJobStatus retrieves live progress of a RAG strategizer
     analyze run by its job id. Use this endpoint to drive a UI progress bar
     while POST /v1/rag-strategizer/analyze runs in the background.

    Args:
        strategize_job_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetRagStrategizerJobStatusResponse
    """

    return sync_detailed(
        strategize_job_id=strategize_job_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    strategize_job_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetRagStrategizerJobStatusResponse]:
    """GetRagStrategizerJobStatus retrieves live progress of a RAG strategizer
     analyze run by its job id. Use this endpoint to drive a UI progress bar
     while POST /v1/rag-strategizer/analyze runs in the background.

    Args:
        strategize_job_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetRagStrategizerJobStatusResponse]
    """

    kwargs = _get_kwargs(
        strategize_job_id=strategize_job_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    strategize_job_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetRagStrategizerJobStatusResponse]:
    """GetRagStrategizerJobStatus retrieves live progress of a RAG strategizer
     analyze run by its job id. Use this endpoint to drive a UI progress bar
     while POST /v1/rag-strategizer/analyze runs in the background.

    Args:
        strategize_job_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetRagStrategizerJobStatusResponse
    """

    return (
        await asyncio_detailed(
            strategize_job_id=strategize_job_id,
            client=client,
        )
    ).parsed
