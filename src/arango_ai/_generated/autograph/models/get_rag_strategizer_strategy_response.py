from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_rag_strategizer_strategy_response_strategy_type_counts import (
        GetRagStrategizerStrategyResponseStrategyTypeCounts,
    )
    from ..models.rag_strategy import RagStrategy


T = TypeVar("T", bound="GetRagStrategizerStrategyResponse")


@_attrs_define
class GetRagStrategizerStrategyResponse:
    """GetRagStrategizerStrategyResponse contains all RAG strategies.

    Attributes:
        strategies (Union[Unset, list['RagStrategy']]):
        total_strategies (Union[Unset, int]):
        strategy_type_counts (Union[Unset, GetRagStrategizerStrategyResponseStrategyTypeCounts]):
    """

    strategies: Union[Unset, list["RagStrategy"]] = UNSET
    total_strategies: Union[Unset, int] = UNSET
    strategy_type_counts: Union[Unset, "GetRagStrategizerStrategyResponseStrategyTypeCounts"] = (
        UNSET
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        strategies: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.strategies, Unset):
            strategies = []
            for strategies_item_data in self.strategies:
                strategies_item = strategies_item_data.to_dict()
                strategies.append(strategies_item)

        total_strategies = self.total_strategies

        strategy_type_counts: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.strategy_type_counts, Unset):
            strategy_type_counts = self.strategy_type_counts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if strategies is not UNSET:
            field_dict["strategies"] = strategies
        if total_strategies is not UNSET:
            field_dict["totalStrategies"] = total_strategies
        if strategy_type_counts is not UNSET:
            field_dict["strategyTypeCounts"] = strategy_type_counts

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.get_rag_strategizer_strategy_response_strategy_type_counts import (
            GetRagStrategizerStrategyResponseStrategyTypeCounts,
        )
        from ..models.rag_strategy import RagStrategy

        d = src_dict.copy()
        strategies = []
        _strategies = d.pop("strategies", UNSET)
        for strategies_item_data in _strategies or []:
            strategies_item = RagStrategy.from_dict(strategies_item_data)

            strategies.append(strategies_item)

        total_strategies = d.pop("totalStrategies", UNSET)

        _strategy_type_counts = d.pop("strategyTypeCounts", UNSET)
        strategy_type_counts: Union[Unset, GetRagStrategizerStrategyResponseStrategyTypeCounts]
        if isinstance(_strategy_type_counts, Unset):
            strategy_type_counts = UNSET
        else:
            strategy_type_counts = GetRagStrategizerStrategyResponseStrategyTypeCounts.from_dict(
                _strategy_type_counts
            )

        get_rag_strategizer_strategy_response = cls(
            strategies=strategies,
            total_strategies=total_strategies,
            strategy_type_counts=strategy_type_counts,
        )

        get_rag_strategizer_strategy_response.additional_properties = d
        return get_rag_strategizer_strategy_response

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
