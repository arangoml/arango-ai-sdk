from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="KnowledgeGraphOverview")


@_attrs_define
class KnowledgeGraphOverview:
    """KnowledgeGraphOverview describes the knowledge graph card on the Overview page.

    Attributes:
        name (Union[Unset, str]):
        status (Union[Unset, str]):
        entity_count (Union[Unset, int]):
        relationship_count (Union[Unset, int]):
        stale (Union[Unset, bool]):
        new_categories (Union[Unset, list[str]]):
        removed_categories (Union[Unset, list[str]]):
    """

    name: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    entity_count: Union[Unset, int] = UNSET
    relationship_count: Union[Unset, int] = UNSET
    stale: Union[Unset, bool] = UNSET
    new_categories: Union[Unset, list[str]] = UNSET
    removed_categories: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        status = self.status

        entity_count = self.entity_count

        relationship_count = self.relationship_count

        stale = self.stale

        new_categories: Union[Unset, list[str]] = UNSET
        if not isinstance(self.new_categories, Unset):
            new_categories = self.new_categories

        removed_categories: Union[Unset, list[str]] = UNSET
        if not isinstance(self.removed_categories, Unset):
            removed_categories = self.removed_categories

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if status is not UNSET:
            field_dict["status"] = status
        if entity_count is not UNSET:
            field_dict["entityCount"] = entity_count
        if relationship_count is not UNSET:
            field_dict["relationshipCount"] = relationship_count
        if stale is not UNSET:
            field_dict["stale"] = stale
        if new_categories is not UNSET:
            field_dict["newCategories"] = new_categories
        if removed_categories is not UNSET:
            field_dict["removedCategories"] = removed_categories

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        status = d.pop("status", UNSET)

        entity_count = d.pop("entityCount", UNSET)

        relationship_count = d.pop("relationshipCount", UNSET)

        stale = d.pop("stale", UNSET)

        new_categories = cast(list[str], d.pop("newCategories", UNSET))

        removed_categories = cast(list[str], d.pop("removedCategories", UNSET))

        knowledge_graph_overview = cls(
            name=name,
            status=status,
            entity_count=entity_count,
            relationship_count=relationship_count,
            stale=stale,
            new_categories=new_categories,
            removed_categories=removed_categories,
        )

        knowledge_graph_overview.additional_properties = d
        return knowledge_graph_overview

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
