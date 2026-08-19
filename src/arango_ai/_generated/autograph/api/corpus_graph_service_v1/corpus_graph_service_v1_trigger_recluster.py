from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.trigger_recluster_request import TriggerReclusterRequest
from ...models.trigger_recluster_response import TriggerReclusterResponse
from ...types import Response


def _get_kwargs(
    *,
    body: TriggerReclusterRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/graph/recluster",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[TriggerReclusterResponse]:
    if response.status_code == 200:
        response_200 = TriggerReclusterResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[TriggerReclusterResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: TriggerReclusterRequest,
) -> Response[TriggerReclusterResponse]:
    """TriggerRecluster manually schedules Layer-3 reclustering for one or more
     partitions. Reclustering is manual-only: AutoGraph tracks per-partition
     divergence and flags needs_reclustering (surfaced on per-file responses and
     persisted on the rags node) once a partition crosses its threshold, but it
     never reclusters on its own -- the user decides whether the recluster
     is worth its cost and invokes this endpoint. Progress and the terminal
     outcome are surfaced via the project-metadata importerOrchestration slot.

     Effectively a MAINTENANCE-WINDOW operation: a recluster claims the single
     service-wide mutation slot and holds it for its whole run (up to ~1h),
     blocking all inserts/updates/deletes/builds meanwhile. Reclusters are
     serialized -- in a multi-partition request only one runs at a time and the
     rest defer (~10s) rather than queueing, staying flagged for a later
     re-trigger -- so reclustering N partitions blocks writes for roughly the sum
     of their run times. Run it during a quiet window and keep batches small (see
     the per-request cap on TriggerReclusterRequest.partition_ids).

    Args:
        body (TriggerReclusterRequest): TriggerReclusterRequest names the RAG partitions to
            recluster. At least one
             partition id is required, and at most a small server-defined maximum per
             request (RECLUSTER_MAX_PARTITIONS_PER_REQUEST) -- reclusters are serialized and
             each blocks all writes for its full run, so oversized batches are rejected
             rather than silently deferring most of the work. Split large reclustering into
             smaller batches, ideally during a maintenance window.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TriggerReclusterResponse]
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
    body: TriggerReclusterRequest,
) -> Optional[TriggerReclusterResponse]:
    """TriggerRecluster manually schedules Layer-3 reclustering for one or more
     partitions. Reclustering is manual-only: AutoGraph tracks per-partition
     divergence and flags needs_reclustering (surfaced on per-file responses and
     persisted on the rags node) once a partition crosses its threshold, but it
     never reclusters on its own -- the user decides whether the recluster
     is worth its cost and invokes this endpoint. Progress and the terminal
     outcome are surfaced via the project-metadata importerOrchestration slot.

     Effectively a MAINTENANCE-WINDOW operation: a recluster claims the single
     service-wide mutation slot and holds it for its whole run (up to ~1h),
     blocking all inserts/updates/deletes/builds meanwhile. Reclusters are
     serialized -- in a multi-partition request only one runs at a time and the
     rest defer (~10s) rather than queueing, staying flagged for a later
     re-trigger -- so reclustering N partitions blocks writes for roughly the sum
     of their run times. Run it during a quiet window and keep batches small (see
     the per-request cap on TriggerReclusterRequest.partition_ids).

    Args:
        body (TriggerReclusterRequest): TriggerReclusterRequest names the RAG partitions to
            recluster. At least one
             partition id is required, and at most a small server-defined maximum per
             request (RECLUSTER_MAX_PARTITIONS_PER_REQUEST) -- reclusters are serialized and
             each blocks all writes for its full run, so oversized batches are rejected
             rather than silently deferring most of the work. Split large reclustering into
             smaller batches, ideally during a maintenance window.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TriggerReclusterResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: TriggerReclusterRequest,
) -> Response[TriggerReclusterResponse]:
    """TriggerRecluster manually schedules Layer-3 reclustering for one or more
     partitions. Reclustering is manual-only: AutoGraph tracks per-partition
     divergence and flags needs_reclustering (surfaced on per-file responses and
     persisted on the rags node) once a partition crosses its threshold, but it
     never reclusters on its own -- the user decides whether the recluster
     is worth its cost and invokes this endpoint. Progress and the terminal
     outcome are surfaced via the project-metadata importerOrchestration slot.

     Effectively a MAINTENANCE-WINDOW operation: a recluster claims the single
     service-wide mutation slot and holds it for its whole run (up to ~1h),
     blocking all inserts/updates/deletes/builds meanwhile. Reclusters are
     serialized -- in a multi-partition request only one runs at a time and the
     rest defer (~10s) rather than queueing, staying flagged for a later
     re-trigger -- so reclustering N partitions blocks writes for roughly the sum
     of their run times. Run it during a quiet window and keep batches small (see
     the per-request cap on TriggerReclusterRequest.partition_ids).

    Args:
        body (TriggerReclusterRequest): TriggerReclusterRequest names the RAG partitions to
            recluster. At least one
             partition id is required, and at most a small server-defined maximum per
             request (RECLUSTER_MAX_PARTITIONS_PER_REQUEST) -- reclusters are serialized and
             each blocks all writes for its full run, so oversized batches are rejected
             rather than silently deferring most of the work. Split large reclustering into
             smaller batches, ideally during a maintenance window.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TriggerReclusterResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: TriggerReclusterRequest,
) -> Optional[TriggerReclusterResponse]:
    """TriggerRecluster manually schedules Layer-3 reclustering for one or more
     partitions. Reclustering is manual-only: AutoGraph tracks per-partition
     divergence and flags needs_reclustering (surfaced on per-file responses and
     persisted on the rags node) once a partition crosses its threshold, but it
     never reclusters on its own -- the user decides whether the recluster
     is worth its cost and invokes this endpoint. Progress and the terminal
     outcome are surfaced via the project-metadata importerOrchestration slot.

     Effectively a MAINTENANCE-WINDOW operation: a recluster claims the single
     service-wide mutation slot and holds it for its whole run (up to ~1h),
     blocking all inserts/updates/deletes/builds meanwhile. Reclusters are
     serialized -- in a multi-partition request only one runs at a time and the
     rest defer (~10s) rather than queueing, staying flagged for a later
     re-trigger -- so reclustering N partitions blocks writes for roughly the sum
     of their run times. Run it during a quiet window and keep batches small (see
     the per-request cap on TriggerReclusterRequest.partition_ids).

    Args:
        body (TriggerReclusterRequest): TriggerReclusterRequest names the RAG partitions to
            recluster. At least one
             partition id is required, and at most a small server-defined maximum per
             request (RECLUSTER_MAX_PARTITIONS_PER_REQUEST) -- reclusters are serialized and
             each blocks all writes for its full run, so oversized batches are rejected
             rather than silently deferring most of the work. Split large reclustering into
             smaller batches, ideally during a maintenance window.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TriggerReclusterResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
