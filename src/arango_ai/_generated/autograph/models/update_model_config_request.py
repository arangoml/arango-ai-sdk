from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="UpdateModelConfigRequest")


@_attrs_define
class UpdateModelConfigRequest:
    """UpdateModelConfigRequest carries the model/provider configuration to persist
    into project metadata (AiProject.model_settings, project-level field 7 in
    the shared project_metadata proto — survives AutoGraph service
    teardown/redeploy). Chat and embedding are configured independently.
    project/service/db are resolved server-side from the deployment environment.
    Project name is validated against the service's configured GENAI_PROJECT_NAME.

       Attributes:
           project (Union[Unset, str]):
           chat_api_provider (Union[Unset, str]):
           embedding_api_provider (Union[Unset, str]):
           chat_model (Union[Unset, str]):
           embedding_model (Union[Unset, str]):
           chat_secret_profile_id (Union[Unset, str]):
           embedding_secret_profile_id (Union[Unset, str]):
           multimodal_model (Union[Unset, str]):
           chat_api_url (Union[Unset, str]):
           embedding_api_url (Union[Unset, str]):
    """

    project: Union[Unset, str] = UNSET
    chat_api_provider: Union[Unset, str] = UNSET
    embedding_api_provider: Union[Unset, str] = UNSET
    chat_model: Union[Unset, str] = UNSET
    embedding_model: Union[Unset, str] = UNSET
    chat_secret_profile_id: Union[Unset, str] = UNSET
    embedding_secret_profile_id: Union[Unset, str] = UNSET
    multimodal_model: Union[Unset, str] = UNSET
    chat_api_url: Union[Unset, str] = UNSET
    embedding_api_url: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project = self.project

        chat_api_provider = self.chat_api_provider

        embedding_api_provider = self.embedding_api_provider

        chat_model = self.chat_model

        embedding_model = self.embedding_model

        chat_secret_profile_id = self.chat_secret_profile_id

        embedding_secret_profile_id = self.embedding_secret_profile_id

        multimodal_model = self.multimodal_model

        chat_api_url = self.chat_api_url

        embedding_api_url = self.embedding_api_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project is not UNSET:
            field_dict["project"] = project
        if chat_api_provider is not UNSET:
            field_dict["chatApiProvider"] = chat_api_provider
        if embedding_api_provider is not UNSET:
            field_dict["embeddingApiProvider"] = embedding_api_provider
        if chat_model is not UNSET:
            field_dict["chatModel"] = chat_model
        if embedding_model is not UNSET:
            field_dict["embeddingModel"] = embedding_model
        if chat_secret_profile_id is not UNSET:
            field_dict["chatSecretProfileId"] = chat_secret_profile_id
        if embedding_secret_profile_id is not UNSET:
            field_dict["embeddingSecretProfileId"] = embedding_secret_profile_id
        if multimodal_model is not UNSET:
            field_dict["multimodalModel"] = multimodal_model
        if chat_api_url is not UNSET:
            field_dict["chatApiUrl"] = chat_api_url
        if embedding_api_url is not UNSET:
            field_dict["embeddingApiUrl"] = embedding_api_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        project = d.pop("project", UNSET)

        chat_api_provider = d.pop("chatApiProvider", UNSET)

        embedding_api_provider = d.pop("embeddingApiProvider", UNSET)

        chat_model = d.pop("chatModel", UNSET)

        embedding_model = d.pop("embeddingModel", UNSET)

        chat_secret_profile_id = d.pop("chatSecretProfileId", UNSET)

        embedding_secret_profile_id = d.pop("embeddingSecretProfileId", UNSET)

        multimodal_model = d.pop("multimodalModel", UNSET)

        chat_api_url = d.pop("chatApiUrl", UNSET)

        embedding_api_url = d.pop("embeddingApiUrl", UNSET)

        update_model_config_request = cls(
            project=project,
            chat_api_provider=chat_api_provider,
            embedding_api_provider=embedding_api_provider,
            chat_model=chat_model,
            embedding_model=embedding_model,
            chat_secret_profile_id=chat_secret_profile_id,
            embedding_secret_profile_id=embedding_secret_profile_id,
            multimodal_model=multimodal_model,
            chat_api_url=chat_api_url,
            embedding_api_url=embedding_api_url,
        )

        update_model_config_request.additional_properties = d
        return update_model_config_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
