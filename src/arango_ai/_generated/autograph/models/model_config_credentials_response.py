from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ModelConfigCredentialsResponse")


@_attrs_define
class ModelConfigCredentialsResponse:
    """ModelConfigCredentialsResponse returns validation status and application
    results for UpdateModelConfig. Always returns HTTP 200; validation failures
    are signaled via valid=false + populated field/error_code/message (clients
    key off these fields, not the HTTP status code).

       Attributes:
           applied (Union[Unset, bool]):
           valid (Union[Unset, bool]):
           applied_to_running_pod (Union[Unset, bool]):
           rebuild_required (Union[Unset, bool]):
           key_status (Union[Unset, str]):
           field (Union[Unset, str]): On validation error (valid=false), these fields are populated:
           error_code (Union[Unset, str]):
           message (Union[Unset, str]):
    """

    applied: Union[Unset, bool] = UNSET
    valid: Union[Unset, bool] = UNSET
    applied_to_running_pod: Union[Unset, bool] = UNSET
    rebuild_required: Union[Unset, bool] = UNSET
    key_status: Union[Unset, str] = UNSET
    field: Union[Unset, str] = UNSET
    error_code: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        applied = self.applied

        valid = self.valid

        applied_to_running_pod = self.applied_to_running_pod

        rebuild_required = self.rebuild_required

        key_status = self.key_status

        field = self.field

        error_code = self.error_code

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if applied is not UNSET:
            field_dict["applied"] = applied
        if valid is not UNSET:
            field_dict["valid"] = valid
        if applied_to_running_pod is not UNSET:
            field_dict["appliedToRunningPod"] = applied_to_running_pod
        if rebuild_required is not UNSET:
            field_dict["rebuildRequired"] = rebuild_required
        if key_status is not UNSET:
            field_dict["keyStatus"] = key_status
        if field is not UNSET:
            field_dict["field"] = field
        if error_code is not UNSET:
            field_dict["errorCode"] = error_code
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        applied = d.pop("applied", UNSET)

        valid = d.pop("valid", UNSET)

        applied_to_running_pod = d.pop("appliedToRunningPod", UNSET)

        rebuild_required = d.pop("rebuildRequired", UNSET)

        key_status = d.pop("keyStatus", UNSET)

        field = d.pop("field", UNSET)

        error_code = d.pop("errorCode", UNSET)

        message = d.pop("message", UNSET)

        model_config_credentials_response = cls(
            applied=applied,
            valid=valid,
            applied_to_running_pod=applied_to_running_pod,
            rebuild_required=rebuild_required,
            key_status=key_status,
            field=field,
            error_code=error_code,
            message=message,
        )

        model_config_credentials_response.additional_properties = d
        return model_config_credentials_response

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
