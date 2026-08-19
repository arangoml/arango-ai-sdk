from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="InsertFileInput")


@_attrs_define
class InsertFileInput:
    """InsertFileInput represents a single File Manager file to insert into an
    existing corpus graph.

       Attributes:
           doc_name (Union[Unset, str]):
           file_id (Union[Unset, str]):
    """

    doc_name: Union[Unset, str] = UNSET
    file_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        doc_name = self.doc_name

        file_id = self.file_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if doc_name is not UNSET:
            field_dict["docName"] = doc_name
        if file_id is not UNSET:
            field_dict["fileId"] = file_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        doc_name = d.pop("docName", UNSET)

        file_id = d.pop("fileId", UNSET)

        insert_file_input = cls(
            doc_name=doc_name,
            file_id=file_id,
        )

        insert_file_input.additional_properties = d
        return insert_file_input

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
