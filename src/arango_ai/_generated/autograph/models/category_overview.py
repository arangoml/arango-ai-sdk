from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="CategoryOverview")


@_attrs_define
class CategoryOverview:
    """CategoryOverview describes one row in the categories list on the Overview page.

    Attributes:
        name (Union[Unset, str]):
        document_count (Union[Unset, int]):
        needs_corpus_update (Union[Unset, bool]):
        needs_strategies (Union[Unset, bool]):
    """

    name: Union[Unset, str] = UNSET
    document_count: Union[Unset, int] = UNSET
    needs_corpus_update: Union[Unset, bool] = UNSET
    needs_strategies: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        document_count = self.document_count

        needs_corpus_update = self.needs_corpus_update

        needs_strategies = self.needs_strategies

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if document_count is not UNSET:
            field_dict["documentCount"] = document_count
        if needs_corpus_update is not UNSET:
            field_dict["needsCorpusUpdate"] = needs_corpus_update
        if needs_strategies is not UNSET:
            field_dict["needsStrategies"] = needs_strategies

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        document_count = d.pop("documentCount", UNSET)

        needs_corpus_update = d.pop("needsCorpusUpdate", UNSET)

        needs_strategies = d.pop("needsStrategies", UNSET)

        category_overview = cls(
            name=name,
            document_count=document_count,
            needs_corpus_update=needs_corpus_update,
            needs_strategies=needs_strategies,
        )

        category_overview.additional_properties = d
        return category_overview

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
