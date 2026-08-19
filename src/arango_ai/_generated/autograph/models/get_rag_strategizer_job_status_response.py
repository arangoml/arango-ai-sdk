from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetRagStrategizerJobStatusResponse")


@_attrs_define
class GetRagStrategizerJobStatusResponse:
    """GetRagStrategizerJobStatusResponse contains live progress of an analyze run.

    Attributes:
        status (Union[Unset, str]):
        progress (Union[Unset, float]):
        clusters_total (Union[Unset, int]):
        clusters_done (Union[Unset, int]):
    """

    status: Union[Unset, str] = UNSET
    progress: Union[Unset, float] = UNSET
    clusters_total: Union[Unset, int] = UNSET
    clusters_done: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        progress = self.progress

        clusters_total = self.clusters_total

        clusters_done = self.clusters_done

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if progress is not UNSET:
            field_dict["progress"] = progress
        if clusters_total is not UNSET:
            field_dict["clustersTotal"] = clusters_total
        if clusters_done is not UNSET:
            field_dict["clustersDone"] = clusters_done

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        status = d.pop("status", UNSET)

        progress = d.pop("progress", UNSET)

        clusters_total = d.pop("clustersTotal", UNSET)

        clusters_done = d.pop("clustersDone", UNSET)

        get_rag_strategizer_job_status_response = cls(
            status=status,
            progress=progress,
            clusters_total=clusters_total,
            clusters_done=clusters_done,
        )

        get_rag_strategizer_job_status_response.additional_properties = d
        return get_rag_strategizer_job_status_response

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
