from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateFileStatus")


@_attrs_define
class UpdateFileStatus:
    """UpdateFileStatus is the per-file outcome of an update. When ``delete_done``
    is true but ``insert_success`` is false, the file was removed from the graph
    and the caller should re-add it via POST /v1/graph/insert.

       Attributes:
           doc_name (Union[Unset, str]):
           delete_done (Union[Unset, bool]):
           insert_success (Union[Unset, bool]):
           error_message (Union[Unset, str]):
           cluster_key (Union[Unset, str]):
           rag_partition_id (Union[Unset, str]):
           file_id (Union[Unset, str]):
           previous_cluster_key (Union[Unset, str]):
    """

    doc_name: Union[Unset, str] = UNSET
    delete_done: Union[Unset, bool] = UNSET
    insert_success: Union[Unset, bool] = UNSET
    error_message: Union[Unset, str] = UNSET
    cluster_key: Union[Unset, str] = UNSET
    rag_partition_id: Union[Unset, str] = UNSET
    file_id: Union[Unset, str] = UNSET
    previous_cluster_key: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        doc_name = self.doc_name

        delete_done = self.delete_done

        insert_success = self.insert_success

        error_message = self.error_message

        cluster_key = self.cluster_key

        rag_partition_id = self.rag_partition_id

        file_id = self.file_id

        previous_cluster_key = self.previous_cluster_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if doc_name is not UNSET:
            field_dict["docName"] = doc_name
        if delete_done is not UNSET:
            field_dict["deleteDone"] = delete_done
        if insert_success is not UNSET:
            field_dict["insertSuccess"] = insert_success
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message
        if cluster_key is not UNSET:
            field_dict["clusterKey"] = cluster_key
        if rag_partition_id is not UNSET:
            field_dict["ragPartitionId"] = rag_partition_id
        if file_id is not UNSET:
            field_dict["fileId"] = file_id
        if previous_cluster_key is not UNSET:
            field_dict["previousClusterKey"] = previous_cluster_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        doc_name = d.pop("docName", UNSET)

        delete_done = d.pop("deleteDone", UNSET)

        insert_success = d.pop("insertSuccess", UNSET)

        error_message = d.pop("errorMessage", UNSET)

        cluster_key = d.pop("clusterKey", UNSET)

        rag_partition_id = d.pop("ragPartitionId", UNSET)

        file_id = d.pop("fileId", UNSET)

        previous_cluster_key = d.pop("previousClusterKey", UNSET)

        update_file_status = cls(
            doc_name=doc_name,
            delete_done=delete_done,
            insert_success=insert_success,
            error_message=error_message,
            cluster_key=cluster_key,
            rag_partition_id=rag_partition_id,
            file_id=file_id,
            previous_cluster_key=previous_cluster_key,
        )

        update_file_status.additional_properties = d
        return update_file_status

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
