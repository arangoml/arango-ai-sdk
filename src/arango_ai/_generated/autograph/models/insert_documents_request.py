from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.insert_file_input import InsertFileInput


T = TypeVar("T", bound="InsertDocumentsRequest")


@_attrs_define
class InsertDocumentsRequest:
    """InsertDocumentsRequest contains a batch of File Manager files to insert into
    an existing corpus graph.

       Attributes:
           files (Union[Unset, list['InsertFileInput']]):
           category (Union[Unset, str]): Category label (e.g. "legal") whose corpus partition scopes similarity +
                clustering, resolved server-side under GENAI_PROJECT_NAME as in
                POST /v1/corpus/builds. Empty resolves to the project's only category;
                required once a project has more than one.
    """

    files: Union[Unset, list["InsertFileInput"]] = UNSET
    category: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.insert_file_input import InsertFileInput

        files: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()
                files.append(files_item)

        category = self.category

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if files is not UNSET:
            field_dict["files"] = files
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

        category = d.pop("category", UNSET)

        insert_documents_request = cls(
            files=files,
            category=category,
        )

        insert_documents_request.additional_properties = d
        return insert_documents_request

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
