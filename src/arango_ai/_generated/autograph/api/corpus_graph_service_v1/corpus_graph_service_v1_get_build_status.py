from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_build_status_response import GetBuildStatusResponse
from ...types import UNSET, Response


def _get_kwargs(
    corpus_build_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/corpus/builds/{corpus_build_id}".format(
            corpus_build_id=corpus_build_id,
        ),
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetBuildStatusResponse]:
    if response.status_code == 200:
        response_200 = GetBuildStatusResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetBuildStatusResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    corpus_build_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetBuildStatusResponse]:
    r"""GetBuildStatus retrieves the current status of a corpus build.

     DEVELOPER NOTE: This endpoint is primarily for monitoring and debugging purposes.
     Since CreateCorpusBuild runs in the background and returns immediately with a
     corpus_build_id, use this endpoint to:
     - Monitor the progress of long-running corpus builds (which can take hours)
     - Check if a build completed successfully or failed
     - Debug issues by viewing error messages and progress percentages
     - Track build lifecycle from \"pending\" → \"running\" → \"completed\"/\"failed\"

     The corpus build process includes: file reading, embedding generation, document
     insertion, vector indexing, similarity finding, clustering, and graph creation.
     Poll this endpoint periodically to track progress through these stages.

    Args:
        corpus_build_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetBuildStatusResponse]
    """

    kwargs = _get_kwargs(
        corpus_build_id=corpus_build_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    corpus_build_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetBuildStatusResponse]:
    r"""GetBuildStatus retrieves the current status of a corpus build.

     DEVELOPER NOTE: This endpoint is primarily for monitoring and debugging purposes.
     Since CreateCorpusBuild runs in the background and returns immediately with a
     corpus_build_id, use this endpoint to:
     - Monitor the progress of long-running corpus builds (which can take hours)
     - Check if a build completed successfully or failed
     - Debug issues by viewing error messages and progress percentages
     - Track build lifecycle from \"pending\" → \"running\" → \"completed\"/\"failed\"

     The corpus build process includes: file reading, embedding generation, document
     insertion, vector indexing, similarity finding, clustering, and graph creation.
     Poll this endpoint periodically to track progress through these stages.

    Args:
        corpus_build_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetBuildStatusResponse
    """

    return sync_detailed(
        corpus_build_id=corpus_build_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    corpus_build_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetBuildStatusResponse]:
    r"""GetBuildStatus retrieves the current status of a corpus build.

     DEVELOPER NOTE: This endpoint is primarily for monitoring and debugging purposes.
     Since CreateCorpusBuild runs in the background and returns immediately with a
     corpus_build_id, use this endpoint to:
     - Monitor the progress of long-running corpus builds (which can take hours)
     - Check if a build completed successfully or failed
     - Debug issues by viewing error messages and progress percentages
     - Track build lifecycle from \"pending\" → \"running\" → \"completed\"/\"failed\"

     The corpus build process includes: file reading, embedding generation, document
     insertion, vector indexing, similarity finding, clustering, and graph creation.
     Poll this endpoint periodically to track progress through these stages.

    Args:
        corpus_build_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetBuildStatusResponse]
    """

    kwargs = _get_kwargs(
        corpus_build_id=corpus_build_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    corpus_build_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetBuildStatusResponse]:
    r"""GetBuildStatus retrieves the current status of a corpus build.

     DEVELOPER NOTE: This endpoint is primarily for monitoring and debugging purposes.
     Since CreateCorpusBuild runs in the background and returns immediately with a
     corpus_build_id, use this endpoint to:
     - Monitor the progress of long-running corpus builds (which can take hours)
     - Check if a build completed successfully or failed
     - Debug issues by viewing error messages and progress percentages
     - Track build lifecycle from \"pending\" → \"running\" → \"completed\"/\"failed\"

     The corpus build process includes: file reading, embedding generation, document
     insertion, vector indexing, similarity finding, clustering, and graph creation.
     Poll this endpoint periodically to track progress through these stages.

    Args:
        corpus_build_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetBuildStatusResponse
    """

    return (
        await asyncio_detailed(
            corpus_build_id=corpus_build_id,
            client=client,
        )
    ).parsed
