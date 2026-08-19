from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateRagStrategizerStrategyRequest")


@_attrs_define
class UpdateRagStrategizerStrategyRequest:
    """UpdateRagStrategizerStrategyRequest contains the fields to override for a cluster strategy.

    Attributes:
        cluster_id (Union[Unset, str]):
        strategy_type (Union[Unset, str]):
        entity_types (Union[Unset, list[str]]):
        extract_images (Union[Unset, bool]):
    """

    cluster_id: Union[Unset, str] = UNSET
    strategy_type: Union[Unset, str] = UNSET
    entity_types: Union[Unset, list[str]] = UNSET
    extract_images: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cluster_id = self.cluster_id

        strategy_type = self.strategy_type

        entity_types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.entity_types, Unset):
            entity_types = self.entity_types

        extract_images = self.extract_images

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cluster_id is not UNSET:
            field_dict["clusterId"] = cluster_id
        if strategy_type is not UNSET:
            field_dict["strategyType"] = strategy_type
        if entity_types is not UNSET:
            field_dict["entityTypes"] = entity_types
        if extract_images is not UNSET:
            field_dict["extractImages"] = extract_images

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        cluster_id = d.pop("clusterId", UNSET)

        strategy_type = d.pop("strategyType", UNSET)

        entity_types = cast(list[str], d.pop("entityTypes", UNSET))

        extract_images = d.pop("extractImages", UNSET)

        update_rag_strategizer_strategy_request = cls(
            cluster_id=cluster_id,
            strategy_type=strategy_type,
            entity_types=entity_types,
            extract_images=extract_images,
        )

        update_rag_strategizer_strategy_request.additional_properties = d
        return update_rag_strategizer_strategy_request

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
