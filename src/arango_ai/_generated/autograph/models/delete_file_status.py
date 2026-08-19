from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.delete_file_status_status import DeleteFileStatusStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteFileStatus")


@_attrs_define
class DeleteFileStatus:
    """
    Attributes:
        file_id (Union[Unset, str]):
        status (Union[Unset, DeleteFileStatusStatus]):
        error_message (Union[Unset, str]):
        rag_partition_id (Union[Unset, str]):
        cluster_key (Union[Unset, str]):
        similarity_edges_removed (Union[Unset, int]):
        divergence_score (Union[Unset, float]):
        needs_reclustering (Union[Unset, bool]):
    """

    file_id: Union[Unset, str] = UNSET
    status: Union[Unset, DeleteFileStatusStatus] = UNSET
    error_message: Union[Unset, str] = UNSET
    rag_partition_id: Union[Unset, str] = UNSET
    cluster_key: Union[Unset, str] = UNSET
    similarity_edges_removed: Union[Unset, int] = UNSET
    divergence_score: Union[Unset, float] = UNSET
    needs_reclustering: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_id = self.file_id

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        error_message = self.error_message

        rag_partition_id = self.rag_partition_id

        cluster_key = self.cluster_key

        similarity_edges_removed = self.similarity_edges_removed

        divergence_score = self.divergence_score

        needs_reclustering = self.needs_reclustering

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file_id is not UNSET:
            field_dict["fileId"] = file_id
        if status is not UNSET:
            field_dict["status"] = status
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message
        if rag_partition_id is not UNSET:
            field_dict["ragPartitionId"] = rag_partition_id
        if cluster_key is not UNSET:
            field_dict["clusterKey"] = cluster_key
        if similarity_edges_removed is not UNSET:
            field_dict["similarityEdgesRemoved"] = similarity_edges_removed
        if divergence_score is not UNSET:
            field_dict["divergenceScore"] = divergence_score
        if needs_reclustering is not UNSET:
            field_dict["needsReclustering"] = needs_reclustering

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        file_id = d.pop("fileId", UNSET)

        _status = d.pop("status", UNSET)
        status: Union[Unset, DeleteFileStatusStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = DeleteFileStatusStatus(_status)

        error_message = d.pop("errorMessage", UNSET)

        rag_partition_id = d.pop("ragPartitionId", UNSET)

        cluster_key = d.pop("clusterKey", UNSET)

        similarity_edges_removed = d.pop("similarityEdgesRemoved", UNSET)

        divergence_score = d.pop("divergenceScore", UNSET)

        needs_reclustering = d.pop("needsReclustering", UNSET)

        delete_file_status = cls(
            file_id=file_id,
            status=status,
            error_message=error_message,
            rag_partition_id=rag_partition_id,
            cluster_key=cluster_key,
            similarity_edges_removed=similarity_edges_removed,
            divergence_score=divergence_score,
            needs_reclustering=needs_reclustering,
        )

        delete_file_status.additional_properties = d
        return delete_file_status

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
