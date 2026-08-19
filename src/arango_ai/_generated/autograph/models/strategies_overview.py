from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union


T = TypeVar("T", bound="StrategiesOverview")


@_attrs_define
class StrategiesOverview:
    """StrategiesOverview describes the strategies block on the Overview page.

    Attributes:
        stale (Union[Unset, bool]):
        categories_without_strategies (Union[Unset, list[str]]):
    """

    stale: Union[Unset, bool] = UNSET
    categories_without_strategies: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        stale = self.stale

        categories_without_strategies: Union[Unset, list[str]] = UNSET
        if not isinstance(self.categories_without_strategies, Unset):
            categories_without_strategies = self.categories_without_strategies

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if stale is not UNSET:
            field_dict["stale"] = stale
        if categories_without_strategies is not UNSET:
            field_dict["categoriesWithoutStrategies"] = categories_without_strategies

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        stale = d.pop("stale", UNSET)

        categories_without_strategies = cast(list[str], d.pop("categoriesWithoutStrategies", UNSET))

        strategies_overview = cls(
            stale=stale,
            categories_without_strategies=categories_without_strategies,
        )

        strategies_overview.additional_properties = d
        return strategies_overview

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
