from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CancelOrchestrationResponse")


@_attrs_define
class CancelOrchestrationResponse:
    """CancelOrchestrationResponse acknowledges a cancellation request.

    Attributes:
        orchestration_id (Union[Unset, str]):
        cancellation_requested (Union[Unset, bool]):
        status (Union[Unset, str]):
        message (Union[Unset, str]):
    """

    orchestration_id: Union[Unset, str] = UNSET
    cancellation_requested: Union[Unset, bool] = UNSET
    status: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        orchestration_id = self.orchestration_id

        cancellation_requested = self.cancellation_requested

        status = self.status

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if orchestration_id is not UNSET:
            field_dict["orchestrationId"] = orchestration_id
        if cancellation_requested is not UNSET:
            field_dict["cancellationRequested"] = cancellation_requested
        if status is not UNSET:
            field_dict["status"] = status
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        orchestration_id = d.pop("orchestrationId", UNSET)

        cancellation_requested = d.pop("cancellationRequested", UNSET)

        status = d.pop("status", UNSET)

        message = d.pop("message", UNSET)

        cancel_orchestration_response = cls(
            orchestration_id=orchestration_id,
            cancellation_requested=cancellation_requested,
            status=status,
            message=message,
        )

        cancel_orchestration_response.additional_properties = d
        return cancel_orchestration_response

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
