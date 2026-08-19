from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="ReclusterPartitionStatus")


@_attrs_define
class ReclusterPartitionStatus:
    """ReclusterPartitionStatus is the per-partition scheduling outcome. The recluster
    itself runs in the background; this only reports whether it was accepted for
    scheduling. For progress, the project-metadata importerOrchestration status slot
    carries the running/completed/failed of a single job at a time -- with several
    partitions their writes overwrite one another, so it is NOT a per-partition
    ledger. The authoritative per-partition outcome is the rags node itself:
    needs_reclustering (cleared on success) and last_reclustered_at; poll those per
    partition when reclustering more than one.

       Attributes:
           rag_partition_id (Union[Unset, str]):
           accepted (Union[Unset, bool]):
           error_message (Union[Unset, str]):
    """

    rag_partition_id: Union[Unset, str] = UNSET
    accepted: Union[Unset, bool] = UNSET
    error_message: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rag_partition_id = self.rag_partition_id

        accepted = self.accepted

        error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rag_partition_id is not UNSET:
            field_dict["ragPartitionId"] = rag_partition_id
        if accepted is not UNSET:
            field_dict["accepted"] = accepted
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        rag_partition_id = d.pop("ragPartitionId", UNSET)

        accepted = d.pop("accepted", UNSET)

        error_message = d.pop("errorMessage", UNSET)

        recluster_partition_status = cls(
            rag_partition_id=rag_partition_id,
            accepted=accepted,
            error_message=error_message,
        )

        recluster_partition_status.additional_properties = d
        return recluster_partition_status

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
