from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.insert_file_input import InsertFileInput


T = TypeVar("T", bound="UpdateDocumentsRequest")


@_attrs_define
class UpdateDocumentsRequest:
    """UpdateDocumentsRequest contains a batch of files to replace in an existing
    corpus graph. Files are referenced by File Manager id, exactly as
    InsertDocumentsRequest does: the replacement content is always read back from
    the File Manager, never sent inline.

       Attributes:
           files (Union[Unset, list['InsertFileInput']]):
           module (Union[Unset, str]):
           category (Union[Unset, str]): Preferred. Category label (bare or already-encoded, see
               InsertDocumentsRequest.category)
                scoping similarity + clustering. Alias for module when module is empty.
    """

    files: Union[Unset, list["InsertFileInput"]] = UNSET
    module: Union[Unset, str] = UNSET
    category: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        files: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()
                files.append(files_item)

        module = self.module

        category = self.category

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if files is not UNSET:
            field_dict["files"] = files
        if module is not UNSET:
            field_dict["module"] = module
        if category is not UNSET:
            field_dict["category"] = category

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.insert_file_input import InsertFileInput

        d = src_dict.copy()
        files = []
        _files = d.pop("files", UNSET)
        for files_item_data in _files or []:
            files_item = InsertFileInput.from_dict(files_item_data)

            files.append(files_item)

        module = d.pop("module", UNSET)

        category = d.pop("category", UNSET)

        update_documents_request = cls(
            files=files,
            module=module,
            category=category,
        )

        update_documents_request.additional_properties = d
        return update_documents_request

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
