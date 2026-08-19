from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.trigger_orchestration_request_importer_env import (
        TriggerOrchestrationRequestImporterEnv,
    )


T = TypeVar("T", bound="TriggerOrchestrationRequest")


@_attrs_define
class TriggerOrchestrationRequest:
    """TriggerOrchestrationRequest contains parameters for the orchestration pipeline.
    Secrets are resolved via secret manager using the profile IDs below.

       Attributes:
           project (Union[Unset, str]):
           replicas (Union[Unset, int]):
           max_retries (Union[Unset, int]):
           importer_env (Union[Unset, TriggerOrchestrationRequestImporterEnv]):
           chat_secret_profile_ids (Union[Unset, list[str]]):
           embedding_secret_profile_id (Union[Unset, str]):
           categories (Union[Unset, list[str]]):
           file_ids (Union[Unset, list[str]]):
    """

    project: Union[Unset, str] = UNSET
    replicas: Union[Unset, int] = UNSET
    max_retries: Union[Unset, int] = UNSET
    importer_env: Union[Unset, "TriggerOrchestrationRequestImporterEnv"] = UNSET
    chat_secret_profile_ids: Union[Unset, list[str]] = UNSET
    embedding_secret_profile_id: Union[Unset, str] = UNSET
    categories: Union[Unset, list[str]] = UNSET
    file_ids: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project = self.project

        replicas = self.replicas

        max_retries = self.max_retries

        importer_env: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.importer_env, Unset):
            importer_env = self.importer_env.to_dict()

        chat_secret_profile_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.chat_secret_profile_ids, Unset):
            chat_secret_profile_ids = self.chat_secret_profile_ids

        embedding_secret_profile_id = self.embedding_secret_profile_id

        categories: Union[Unset, list[str]] = UNSET
        if not isinstance(self.categories, Unset):
            categories = self.categories

        file_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.file_ids, Unset):
            file_ids = self.file_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project is not UNSET:
            field_dict["project"] = project
        if replicas is not UNSET:
            field_dict["replicas"] = replicas
        if max_retries is not UNSET:
            field_dict["maxRetries"] = max_retries
        if importer_env is not UNSET:
            field_dict["importerEnv"] = importer_env
        if chat_secret_profile_ids is not UNSET:
            field_dict["chatSecretProfileIds"] = chat_secret_profile_ids
        if embedding_secret_profile_id is not UNSET:
            field_dict["embeddingSecretProfileId"] = embedding_secret_profile_id
        if categories is not UNSET:
            field_dict["categories"] = categories
        if file_ids is not UNSET:
            field_dict["fileIds"] = file_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.trigger_orchestration_request_importer_env import (
            TriggerOrchestrationRequestImporterEnv,
        )

        d = src_dict.copy()
        project = d.pop("project", UNSET)

        replicas = d.pop("replicas", UNSET)

        max_retries = d.pop("maxRetries", UNSET)

        _importer_env = d.pop("importerEnv", UNSET)
        importer_env: Union[Unset, TriggerOrchestrationRequestImporterEnv]
        if isinstance(_importer_env, Unset):
            importer_env = UNSET
        else:
            importer_env = TriggerOrchestrationRequestImporterEnv.from_dict(_importer_env)

        chat_secret_profile_ids = cast(list[str], d.pop("chatSecretProfileIds", UNSET))

        embedding_secret_profile_id = d.pop("embeddingSecretProfileId", UNSET)

        categories = cast(list[str], d.pop("categories", UNSET))

        file_ids = cast(list[str], d.pop("fileIds", UNSET))

        trigger_orchestration_request = cls(
            project=project,
            replicas=replicas,
            max_retries=max_retries,
            importer_env=importer_env,
            chat_secret_profile_ids=chat_secret_profile_ids,
            embedding_secret_profile_id=embedding_secret_profile_id,
            categories=categories,
            file_ids=file_ids,
        )

        trigger_orchestration_request.additional_properties = d
        return trigger_orchestration_request

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
