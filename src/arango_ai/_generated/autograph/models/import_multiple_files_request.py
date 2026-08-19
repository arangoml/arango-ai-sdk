from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_input import FileInput


T = TypeVar("T", bound="ImportMultipleFilesRequest")


@_attrs_define
class ImportMultipleFilesRequest:
    """ImportMultipleFilesRequest contains the files to be imported.

    Attributes:
        files (Union[Unset, list['FileInput']]):
        module (Union[Unset, str]):
    """

    files: Union[Unset, list["FileInput"]] = UNSET
    module: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.file_input import FileInput

        files: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()
                files.append(files_item)

        module = self.module

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if files is not UNSET:
            field_dict["files"] = files
        if module is not UNSET:
            field_dict["module"] = module

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.file_input import FileInput

        d = src_dict.copy()
        files = []
        _files = d.pop("files", UNSET)
        for files_item_data in _files or []:
            files_item = FileInput.from_dict(files_item_data)

            files.append(files_item)

        module = d.pop("module", UNSET)

        import_multiple_files_request = cls(
            files=files,
            module=module,
        )

        import_multiple_files_request.additional_properties = d
        return import_multiple_files_request

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
