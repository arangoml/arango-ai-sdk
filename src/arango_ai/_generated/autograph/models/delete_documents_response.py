from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.delete_documents_response_overall_status import DeleteDocumentsResponseOverallStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.delete_file_status import DeleteFileStatus
    from ..models.layer_3_partition_delete_result import Layer3PartitionDeleteResult


T = TypeVar("T", bound="DeleteDocumentsResponse")


@_attrs_define
class DeleteDocumentsResponse:
    """
    Attributes:
        results (Union[Unset, list['DeleteFileStatus']]):
        affected_rag_partitions (Union[Unset, list[str]]):
        removed_rag_partitions (Union[Unset, list[str]]):
        layer_3_results (Union[Unset, list['Layer3PartitionDeleteResult']]):
        overall_status (Union[Unset, DeleteDocumentsResponseOverallStatus]):
        affected_cluster_ids (Union[Unset, list[str]]):
        removed_cluster_ids (Union[Unset, list[str]]):
        delete_id (Union[Unset, str]):
    """

    results: Union[Unset, list["DeleteFileStatus"]] = UNSET
    affected_rag_partitions: Union[Unset, list[str]] = UNSET
    removed_rag_partitions: Union[Unset, list[str]] = UNSET
    layer_3_results: Union[Unset, list["Layer3PartitionDeleteResult"]] = UNSET
    overall_status: Union[Unset, DeleteDocumentsResponseOverallStatus] = UNSET
    affected_cluster_ids: Union[Unset, list[str]] = UNSET
    removed_cluster_ids: Union[Unset, list[str]] = UNSET
    delete_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        results: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.results, Unset):
            results = []
            for results_item_data in self.results:
                results_item = results_item_data.to_dict()
                results.append(results_item)

        affected_rag_partitions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.affected_rag_partitions, Unset):
            affected_rag_partitions = self.affected_rag_partitions

        removed_rag_partitions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.removed_rag_partitions, Unset):
            removed_rag_partitions = self.removed_rag_partitions

        layer_3_results: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.layer_3_results, Unset):
            layer_3_results = []
            for layer_3_results_item_data in self.layer_3_results:
                layer_3_results_item = layer_3_results_item_data.to_dict()
                layer_3_results.append(layer_3_results_item)

        overall_status: Union[Unset, str] = UNSET
        if not isinstance(self.overall_status, Unset):
            overall_status = self.overall_status.value

        affected_cluster_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.affected_cluster_ids, Unset):
            affected_cluster_ids = self.affected_cluster_ids

        removed_cluster_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.removed_cluster_ids, Unset):
            removed_cluster_ids = self.removed_cluster_ids

        delete_id = self.delete_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if results is not UNSET:
            field_dict["results"] = results
        if affected_rag_partitions is not UNSET:
            field_dict["affectedRagPartitions"] = affected_rag_partitions
        if removed_rag_partitions is not UNSET:
            field_dict["removedRagPartitions"] = removed_rag_partitions
        if layer_3_results is not UNSET:
            field_dict["layer3Results"] = layer_3_results
        if overall_status is not UNSET:
            field_dict["overallStatus"] = overall_status
        if affected_cluster_ids is not UNSET:
            field_dict["affectedClusterIds"] = affected_cluster_ids
        if removed_cluster_ids is not UNSET:
            field_dict["removedClusterIds"] = removed_cluster_ids
        if delete_id is not UNSET:
            field_dict["deleteId"] = delete_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.delete_file_status import DeleteFileStatus
        from ..models.layer_3_partition_delete_result import Layer3PartitionDeleteResult

        d = src_dict.copy()
        results = []
        _results = d.pop("results", UNSET)
        for results_item_data in _results or []:
            results_item = DeleteFileStatus.from_dict(results_item_data)

            results.append(results_item)

        affected_rag_partitions = cast(list[str], d.pop("affectedRagPartitions", UNSET))

        removed_rag_partitions = cast(list[str], d.pop("removedRagPartitions", UNSET))

        layer_3_results = []
        _layer_3_results = d.pop("layer3Results", UNSET)
        for layer_3_results_item_data in _layer_3_results or []:
            layer_3_results_item = Layer3PartitionDeleteResult.from_dict(layer_3_results_item_data)

            layer_3_results.append(layer_3_results_item)

        _overall_status = d.pop("overallStatus", UNSET)
        overall_status: Union[Unset, DeleteDocumentsResponseOverallStatus]
        if isinstance(_overall_status, Unset):
            overall_status = UNSET
        else:
            overall_status = DeleteDocumentsResponseOverallStatus(_overall_status)

        affected_cluster_ids = cast(list[str], d.pop("affectedClusterIds", UNSET))

        removed_cluster_ids = cast(list[str], d.pop("removedClusterIds", UNSET))

        delete_id = d.pop("deleteId", UNSET)

        delete_documents_response = cls(
            results=results,
            affected_rag_partitions=affected_rag_partitions,
            removed_rag_partitions=removed_rag_partitions,
            layer_3_results=layer_3_results,
            overall_status=overall_status,
            affected_cluster_ids=affected_cluster_ids,
            removed_cluster_ids=removed_cluster_ids,
            delete_id=delete_id,
        )

        delete_documents_response.additional_properties = d
        return delete_documents_response

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
