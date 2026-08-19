from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TriggerReclusterRequest")


@_attrs_define
class TriggerReclusterRequest:
    """TriggerReclusterRequest names the RAG partitions to recluster. At least one
    partition id is required, and at most a small server-defined maximum per
    request (RECLUSTER_MAX_PARTITIONS_PER_REQUEST) -- reclusters are serialized and
    each blocks all writes for its full run, so oversized batches are rejected
    rather than silently deferring most of the work. Split large reclustering into
    smaller batches, ideally during a maintenance window.

       Attributes:
           partition_ids (Union[Unset, list[str]]):
    """

    partition_ids: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        partition_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.partition_ids, Unset):
            partition_ids = self.partition_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if partition_ids is not UNSET:
            field_dict["partitionIds"] = partition_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        partition_ids = cast(list[str], d.pop("partitionIds", UNSET))

        trigger_recluster_request = cls(
            partition_ids=partition_ids,
        )

        trigger_recluster_request.additional_properties = d
        return trigger_recluster_request

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
