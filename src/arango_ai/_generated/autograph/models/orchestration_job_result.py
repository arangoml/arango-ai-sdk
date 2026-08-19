from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union


T = TypeVar("T", bound="OrchestrationJobResult")


@_attrs_define
class OrchestrationJobResult:
    """OrchestrationJobResult contains the outcome of a single orchestration job.

    Attributes:
        rag_partition_id (Union[Unset, str]):
        strategy_type (Union[Unset, str]):
        status (Union[Unset, str]):
        retry_count (Union[Unset, int]):
        error_message (Union[Unset, str]):
        category (Union[Unset, str]):
        divergence_score (Union[Unset, float]): AIS-1444: the partition's divergence, computed at the right time --
            right
             after Layer 3 actually created/grew this partition's entities. This is the
             authoritative score (the insert/update responses no longer carry a premature
             one); it is also persisted on the rags node. Populated on the terminal poll
             once the job is completed.
        needs_reclustering (Union[Unset, bool]):
    """

    rag_partition_id: Union[Unset, str] = UNSET
    strategy_type: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    retry_count: Union[Unset, int] = UNSET
    error_message: Union[Unset, str] = UNSET
    category: Union[Unset, str] = UNSET
    divergence_score: Union[Unset, float] = UNSET
    needs_reclustering: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rag_partition_id = self.rag_partition_id

        strategy_type = self.strategy_type

        status = self.status

        retry_count = self.retry_count

        error_message = self.error_message

        category = self.category

        divergence_score = self.divergence_score

        needs_reclustering = self.needs_reclustering

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rag_partition_id is not UNSET:
            field_dict["ragPartitionId"] = rag_partition_id
        if strategy_type is not UNSET:
            field_dict["strategyType"] = strategy_type
        if status is not UNSET:
            field_dict["status"] = status
        if retry_count is not UNSET:
            field_dict["retryCount"] = retry_count
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message
        if category is not UNSET:
            field_dict["category"] = category
        if divergence_score is not UNSET:
            field_dict["divergenceScore"] = divergence_score
        if needs_reclustering is not UNSET:
            field_dict["needsReclustering"] = needs_reclustering

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        rag_partition_id = d.pop("ragPartitionId", UNSET)

        strategy_type = d.pop("strategyType", UNSET)

        status = d.pop("status", UNSET)

        retry_count = d.pop("retryCount", UNSET)

        error_message = d.pop("errorMessage", UNSET)

        category = d.pop("category", UNSET)

        divergence_score = d.pop("divergenceScore", UNSET)

        needs_reclustering = d.pop("needsReclustering", UNSET)

        orchestration_job_result = cls(
            rag_partition_id=rag_partition_id,
            strategy_type=strategy_type,
            status=status,
            retry_count=retry_count,
            error_message=error_message,
            category=category,
            divergence_score=divergence_score,
            needs_reclustering=needs_reclustering,
        )

        orchestration_job_result.additional_properties = d
        return orchestration_job_result

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
