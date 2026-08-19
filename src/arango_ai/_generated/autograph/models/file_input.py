from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FileInput")


@_attrs_define
class FileInput:
    """FileInput represents a single file to be imported with inline content.

    Attributes:
        doc_name (Union[Unset, str]):
        content (Union[Unset, str]):
        citable_url (Union[Unset, str]):
        metadata (Union[Unset, str]):
    """

    doc_name: Union[Unset, str] = UNSET
    content: Union[Unset, str] = UNSET
    citable_url: Union[Unset, str] = UNSET
    metadata: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        doc_name = self.doc_name

        content = self.content

        citable_url = self.citable_url

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if doc_name is not UNSET:
            field_dict["docName"] = doc_name
        if content is not UNSET:
            field_dict["content"] = content
        if citable_url is not UNSET:
            field_dict["citableUrl"] = citable_url
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        doc_name = d.pop("docName", UNSET)

        content = d.pop("content", UNSET)

        citable_url = d.pop("citableUrl", UNSET)

        metadata = d.pop("metadata", UNSET)

        file_input = cls(
            doc_name=doc_name,
            content=content,
            citable_url=citable_url,
            metadata=metadata,
        )

        file_input.additional_properties = d
        return file_input

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
