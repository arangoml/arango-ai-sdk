from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union


T = TypeVar("T", bound="DeleteCategoryResponse")


@_attrs_define
class DeleteCategoryResponse:
    """DeleteCategoryResponse reports the synchronous delete outcome.

    Attributes:
        deleted (Union[Unset, bool]):
        category (Union[Unset, str]):
        graph_updated (Union[Unset, bool]):
        files_deleted (Union[Unset, int]):
        locked_skipped (Union[Unset, list[str]]):
    """

    deleted: Union[Unset, bool] = UNSET
    category: Union[Unset, str] = UNSET
    graph_updated: Union[Unset, bool] = UNSET
    files_deleted: Union[Unset, int] = UNSET
    locked_skipped: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deleted = self.deleted

        category = self.category

        graph_updated = self.graph_updated

        files_deleted = self.files_deleted

        locked_skipped: Union[Unset, list[str]] = UNSET
        if not isinstance(self.locked_skipped, Unset):
            locked_skipped = self.locked_skipped

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if category is not UNSET:
            field_dict["category"] = category
        if graph_updated is not UNSET:
            field_dict["graphUpdated"] = graph_updated
        if files_deleted is not UNSET:
            field_dict["filesDeleted"] = files_deleted
        if locked_skipped is not UNSET:
            field_dict["lockedSkipped"] = locked_skipped

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        deleted = d.pop("deleted", UNSET)

        category = d.pop("category", UNSET)

        graph_updated = d.pop("graphUpdated", UNSET)

        files_deleted = d.pop("filesDeleted", UNSET)

        locked_skipped = cast(list[str], d.pop("lockedSkipped", UNSET))

        delete_category_response = cls(
            deleted=deleted,
            category=category,
            graph_updated=graph_updated,
            files_deleted=files_deleted,
            locked_skipped=locked_skipped,
        )

        delete_category_response.additional_properties = d
        return delete_category_response

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
