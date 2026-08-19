from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union


T = TypeVar("T", bound="DeleteDocumentsRequest")


@_attrs_define
class DeleteDocumentsRequest:
    """
    Attributes:
        file_ids (Union[Unset, list[str]]):
        doc_names (Union[Unset, list[str]]):
        category (Union[Unset, str]):
    """

    file_ids: Union[Unset, list[str]] = UNSET
    doc_names: Union[Unset, list[str]] = UNSET
    category: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.file_ids, Unset):
            file_ids = self.file_ids

        doc_names: Union[Unset, list[str]] = UNSET
        if not isinstance(self.doc_names, Unset):
            doc_names = self.doc_names

        category = self.category

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file_ids is not UNSET:
            field_dict["fileIds"] = file_ids
        if doc_names is not UNSET:
            field_dict["docNames"] = doc_names
        if category is not UNSET:
            field_dict["category"] = category

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        file_ids = cast(list[str], d.pop("fileIds", UNSET))

        doc_names = cast(list[str], d.pop("docNames", UNSET))

        category = d.pop("category", UNSET)

        delete_documents_request = cls(
            file_ids=file_ids,
            doc_names=doc_names,
            category=category,
        )

        delete_documents_request.additional_properties = d
        return delete_documents_request

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
