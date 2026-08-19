from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union

if TYPE_CHECKING:
    from ..models.rag_strategy import RagStrategy


T = TypeVar("T", bound="UpdateRagStrategizerStrategyResponse")


@_attrs_define
class UpdateRagStrategizerStrategyResponse:
    """UpdateRagStrategizerStrategyResponse returns the updated strategy.

    Attributes:
        strategy (Union[Unset, RagStrategy]): RagStrategy represents a single RAG strategy for a cluster/domain.
    """

    strategy: Union[Unset, "RagStrategy"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        strategy: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.strategy, Unset):
            strategy = self.strategy.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if strategy is not UNSET:
            field_dict["strategy"] = strategy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.rag_strategy import RagStrategy

        d = src_dict.copy()
        _strategy = d.pop("strategy", UNSET)
        strategy: Union[Unset, RagStrategy]
        if isinstance(_strategy, Unset):
            strategy = UNSET
        else:
            strategy = RagStrategy.from_dict(_strategy)

        update_rag_strategizer_strategy_response = cls(
            strategy=strategy,
        )

        update_rag_strategizer_strategy_response.additional_properties = d
        return update_rag_strategizer_strategy_response

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
