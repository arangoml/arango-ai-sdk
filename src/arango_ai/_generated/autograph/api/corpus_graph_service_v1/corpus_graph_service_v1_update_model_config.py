from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.model_config_credentials_response import ModelConfigCredentialsResponse
from ...models.update_model_config_request import UpdateModelConfigRequest
from ...types import UNSET, Response


def _get_kwargs(
    project: str,
    *,
    body: UpdateModelConfigRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/v1/projects/{project}/model-config/credentials".format(
            project=project,
        ),
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ModelConfigCredentialsResponse]:
    if response.status_code == 200:
        response_200 = ModelConfigCredentialsResponse.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ModelConfigCredentialsResponse]:
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
    body: UpdateModelConfigRequest,
) -> Response[ModelConfigCredentialsResponse]:
    r"""UpdateModelConfig persists the AutoGraph model/provider configuration with
     inline validation, in-place pod updates, and diff-then-write metadata
     persistence. Validates provider/model/key inline and applies changes to
     the running pod without rebuild (no idle-only restriction).
     Chat providers: \"openai\" | \"triton\" | \"custom\". Embedding: \"openai\" | \"custom\".
     `custom` is an OpenAI-compatible endpoint; only client construction maps it to openai.
     All fields required except multimodal_model (optional) and chat_api_url /
     embedding_api_url (optional unless the corresponding provider is \"custom\",
     in which case that URL is required).

    Args:
        project (str):
        body (UpdateModelConfigRequest): UpdateModelConfigRequest carries the model/provider
            configuration to persist
             into project metadata (AiProject.model_settings, project-level field 7 in
             the shared project_metadata proto — survives AutoGraph service
             teardown/redeploy). Chat and embedding are configured independently.
             project/service/db are resolved server-side from the deployment environment.
             Project name is validated against the service's configured GENAI_PROJECT_NAME.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ModelConfigCredentialsResponse]
    """

    kwargs = _get_kwargs(
        project=project,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateModelConfigRequest,
) -> Optional[ModelConfigCredentialsResponse]:
    r"""UpdateModelConfig persists the AutoGraph model/provider configuration with
     inline validation, in-place pod updates, and diff-then-write metadata
     persistence. Validates provider/model/key inline and applies changes to
     the running pod without rebuild (no idle-only restriction).
     Chat providers: \"openai\" | \"triton\" | \"custom\". Embedding: \"openai\" | \"custom\".
     `custom` is an OpenAI-compatible endpoint; only client construction maps it to openai.
     All fields required except multimodal_model (optional) and chat_api_url /
     embedding_api_url (optional unless the corresponding provider is \"custom\",
     in which case that URL is required).

    Args:
        project (str):
        body (UpdateModelConfigRequest): UpdateModelConfigRequest carries the model/provider
            configuration to persist
             into project metadata (AiProject.model_settings, project-level field 7 in
             the shared project_metadata proto — survives AutoGraph service
             teardown/redeploy). Chat and embedding are configured independently.
             project/service/db are resolved server-side from the deployment environment.
             Project name is validated against the service's configured GENAI_PROJECT_NAME.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ModelConfigCredentialsResponse
    """

    return sync_detailed(
        project=project,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    project: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateModelConfigRequest,
) -> Response[ModelConfigCredentialsResponse]:
    r"""UpdateModelConfig persists the AutoGraph model/provider configuration with
     inline validation, in-place pod updates, and diff-then-write metadata
     persistence. Validates provider/model/key inline and applies changes to
     the running pod without rebuild (no idle-only restriction).
     Chat providers: \"openai\" | \"triton\" | \"custom\". Embedding: \"openai\" | \"custom\".
     `custom` is an OpenAI-compatible endpoint; only client construction maps it to openai.
     All fields required except multimodal_model (optional) and chat_api_url /
     embedding_api_url (optional unless the corresponding provider is \"custom\",
     in which case that URL is required).

    Args:
        project (str):
        body (UpdateModelConfigRequest): UpdateModelConfigRequest carries the model/provider
            configuration to persist
             into project metadata (AiProject.model_settings, project-level field 7 in
             the shared project_metadata proto — survives AutoGraph service
             teardown/redeploy). Chat and embedding are configured independently.
             project/service/db are resolved server-side from the deployment environment.
             Project name is validated against the service's configured GENAI_PROJECT_NAME.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ModelConfigCredentialsResponse]
    """

    kwargs = _get_kwargs(
        project=project,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UpdateModelConfigRequest,
) -> Optional[ModelConfigCredentialsResponse]:
    r"""UpdateModelConfig persists the AutoGraph model/provider configuration with
     inline validation, in-place pod updates, and diff-then-write metadata
     persistence. Validates provider/model/key inline and applies changes to
     the running pod without rebuild (no idle-only restriction).
     Chat providers: \"openai\" | \"triton\" | \"custom\". Embedding: \"openai\" | \"custom\".
     `custom` is an OpenAI-compatible endpoint; only client construction maps it to openai.
     All fields required except multimodal_model (optional) and chat_api_url /
     embedding_api_url (optional unless the corresponding provider is \"custom\",
     in which case that URL is required).

    Args:
        project (str):
        body (UpdateModelConfigRequest): UpdateModelConfigRequest carries the model/provider
            configuration to persist
             into project metadata (AiProject.model_settings, project-level field 7 in
             the shared project_metadata proto — survives AutoGraph service
             teardown/redeploy). Chat and embedding are configured independently.
             project/service/db are resolved server-side from the deployment environment.
             Project name is validated against the service's configured GENAI_PROJECT_NAME.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ModelConfigCredentialsResponse
    """

    return (
        await asyncio_detailed(
            project=project,
            client=client,
            body=body,
        )
    ).parsed
