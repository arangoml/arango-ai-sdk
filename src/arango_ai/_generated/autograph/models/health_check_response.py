from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="HealthCheckResponse")


@_attrs_define
class HealthCheckResponse:
    """HealthCheckResponse contains the health status of the service.

    Attributes:
        status (Union[Unset, str]): status can be "SERVING" or "NOT_SERVING"
        message (Union[Unset, str]): message carries an optional human-readable detail. When customer LLM
             tracing (AIS-1530) is enabled it holds a JSON per-provider health
             snapshot; otherwise a short status string. Consumers keying on `status`
             are unaffected.
    """

    status: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        status = d.pop("status", UNSET)

        message = d.pop("message", UNSET)

        health_check_response = cls(
            status=status,
            message=message,
        )

        health_check_response.additional_properties = d
        return health_check_response

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
