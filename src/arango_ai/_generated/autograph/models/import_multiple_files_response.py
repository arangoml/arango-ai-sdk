from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="ImportMultipleFilesResponse")


@_attrs_define
class ImportMultipleFilesResponse:
    """ImportMultipleFilesResponse contains the result of the import operation.

    Attributes:
        success (Union[Unset, bool]):
        message (Union[Unset, str]):
        error_message (Union[Unset, str]):
    """

    success: Union[Unset, bool] = UNSET
    message: Union[Unset, str] = UNSET
    error_message: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        message = self.message

        error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if success is not UNSET:
            field_dict["success"] = success
        if message is not UNSET:
            field_dict["message"] = message
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        success = d.pop("success", UNSET)

        message = d.pop("message", UNSET)

        error_message = d.pop("errorMessage", UNSET)

        import_multiple_files_response = cls(
            success=success,
            message=message,
            error_message=error_message,
        )

        import_multiple_files_response.additional_properties = d
        return import_multiple_files_response

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
