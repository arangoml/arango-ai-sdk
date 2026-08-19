from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union

if TYPE_CHECKING:
    from ..models.rag_strategy_parameters import RagStrategyParameters


T = TypeVar("T", bound="RagStrategy")


@_attrs_define
class RagStrategy:
    """RagStrategy represents a single RAG strategy for a cluster/domain.

    Attributes:
        cluster_id (Union[Unset, str]):
        strategy_type (Union[Unset, str]):
        rag_partition_id (Union[Unset, str]):
        entity_types (Union[Unset, list[str]]):
        document_count (Union[Unset, int]):
        parameters (Union[Unset, RagStrategyParameters]):
    """

    cluster_id: Union[Unset, str] = UNSET
    strategy_type: Union[Unset, str] = UNSET
    rag_partition_id: Union[Unset, str] = UNSET
    entity_types: Union[Unset, list[str]] = UNSET
    document_count: Union[Unset, int] = UNSET
    parameters: Union[Unset, "RagStrategyParameters"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cluster_id = self.cluster_id

        strategy_type = self.strategy_type

        rag_partition_id = self.rag_partition_id

        entity_types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.entity_types, Unset):
            entity_types = self.entity_types

        document_count = self.document_count

        parameters: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cluster_id is not UNSET:
            field_dict["clusterId"] = cluster_id
        if strategy_type is not UNSET:
            field_dict["strategyType"] = strategy_type
        if rag_partition_id is not UNSET:
            field_dict["ragPartitionId"] = rag_partition_id
        if entity_types is not UNSET:
            field_dict["entityTypes"] = entity_types
        if document_count is not UNSET:
            field_dict["documentCount"] = document_count
        if parameters is not UNSET:
            field_dict["parameters"] = parameters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.rag_strategy_parameters import RagStrategyParameters

        d = src_dict.copy()
        cluster_id = d.pop("clusterId", UNSET)

        strategy_type = d.pop("strategyType", UNSET)

        rag_partition_id = d.pop("ragPartitionId", UNSET)

        entity_types = cast(list[str], d.pop("entityTypes", UNSET))

        document_count = d.pop("documentCount", UNSET)

        _parameters = d.pop("parameters", UNSET)
        parameters: Union[Unset, RagStrategyParameters]
        if isinstance(_parameters, Unset):
            parameters = UNSET
        else:
            parameters = RagStrategyParameters.from_dict(_parameters)

        rag_strategy = cls(
            cluster_id=cluster_id,
            strategy_type=strategy_type,
            rag_partition_id=rag_partition_id,
            entity_types=entity_types,
            document_count=document_count,
            parameters=parameters,
        )

        rag_strategy.additional_properties = d
        return rag_strategy

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
