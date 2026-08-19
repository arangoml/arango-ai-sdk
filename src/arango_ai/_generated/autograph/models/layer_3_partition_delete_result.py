from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.layer_3_partition_delete_result_status import (
    Layer3PartitionDeleteResultStatus,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="Layer3PartitionDeleteResult")


@_attrs_define
class Layer3PartitionDeleteResult:
    """Per-partition result of the Layer-3 delete. Counts are Autograph's own AQL
    removal totals for that partition's batch.

       Attributes:
           rag_partition_id (Union[Unset, str]):
           status (Union[Unset, Layer3PartitionDeleteResultStatus]):
           error_message (Union[Unset, str]):
           documents_removed (Union[Unset, int]):
           chunks_removed (Union[Unset, int]):
           entities_removed (Union[Unset, int]):
           communities_removed (Union[Unset, int]):
           semantic_units_removed (Union[Unset, int]):
           edges_removed (Union[Unset, int]):
    """

    rag_partition_id: Union[Unset, str] = UNSET
    status: Union[Unset, Layer3PartitionDeleteResultStatus] = UNSET
    error_message: Union[Unset, str] = UNSET
    documents_removed: Union[Unset, int] = UNSET
    chunks_removed: Union[Unset, int] = UNSET
    entities_removed: Union[Unset, int] = UNSET
    communities_removed: Union[Unset, int] = UNSET
    semantic_units_removed: Union[Unset, int] = UNSET
    edges_removed: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rag_partition_id = self.rag_partition_id

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        error_message = self.error_message

        documents_removed = self.documents_removed

        chunks_removed = self.chunks_removed

        entities_removed = self.entities_removed

        communities_removed = self.communities_removed

        semantic_units_removed = self.semantic_units_removed

        edges_removed = self.edges_removed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rag_partition_id is not UNSET:
            field_dict["ragPartitionId"] = rag_partition_id
        if status is not UNSET:
            field_dict["status"] = status
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message
        if documents_removed is not UNSET:
            field_dict["documentsRemoved"] = documents_removed
        if chunks_removed is not UNSET:
            field_dict["chunksRemoved"] = chunks_removed
        if entities_removed is not UNSET:
            field_dict["entitiesRemoved"] = entities_removed
        if communities_removed is not UNSET:
            field_dict["communitiesRemoved"] = communities_removed
        if semantic_units_removed is not UNSET:
            field_dict["semanticUnitsRemoved"] = semantic_units_removed
        if edges_removed is not UNSET:
            field_dict["edgesRemoved"] = edges_removed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        rag_partition_id = d.pop("ragPartitionId", UNSET)

        _status = d.pop("status", UNSET)
        status: Union[Unset, Layer3PartitionDeleteResultStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = Layer3PartitionDeleteResultStatus(_status)

        error_message = d.pop("errorMessage", UNSET)

        documents_removed = d.pop("documentsRemoved", UNSET)

        chunks_removed = d.pop("chunksRemoved", UNSET)

        entities_removed = d.pop("entitiesRemoved", UNSET)

        communities_removed = d.pop("communitiesRemoved", UNSET)

        semantic_units_removed = d.pop("semanticUnitsRemoved", UNSET)

        edges_removed = d.pop("edgesRemoved", UNSET)

        layer_3_partition_delete_result = cls(
            rag_partition_id=rag_partition_id,
            status=status,
            error_message=error_message,
            documents_removed=documents_removed,
            chunks_removed=chunks_removed,
            entities_removed=entities_removed,
            communities_removed=communities_removed,
            semantic_units_removed=semantic_units_removed,
            edges_removed=edges_removed,
        )

        layer_3_partition_delete_result.additional_properties = d
        return layer_3_partition_delete_result

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
