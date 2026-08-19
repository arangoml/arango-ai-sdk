from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="InsertFileStatus")


@_attrs_define
class InsertFileStatus:
    """InsertFileStatus is the per-file outcome of an insert.

    Attributes:
        doc_name (Union[Unset, str]):
        success (Union[Unset, bool]):
        error_message (Union[Unset, str]):
        rag_partition_id (Union[Unset, str]):
        cluster_key (Union[Unset, str]):
        file_id (Union[Unset, str]):
    """

    doc_name: Union[Unset, str] = UNSET
    success: Union[Unset, bool] = UNSET
    error_message: Union[Unset, str] = UNSET
    rag_partition_id: Union[Unset, str] = UNSET
    cluster_key: Union[Unset, str] = UNSET
    file_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        doc_name = self.doc_name

        success = self.success

        error_message = self.error_message

        rag_partition_id = self.rag_partition_id

        cluster_key = self.cluster_key

        file_id = self.file_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if doc_name is not UNSET:
            field_dict["docName"] = doc_name
        if success is not UNSET:
            field_dict["success"] = success
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message
        if rag_partition_id is not UNSET:
            field_dict["ragPartitionId"] = rag_partition_id
        if cluster_key is not UNSET:
            field_dict["clusterKey"] = cluster_key
        if file_id is not UNSET:
            field_dict["fileId"] = file_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        doc_name = d.pop("docName", UNSET)

        success = d.pop("success", UNSET)

        error_message = d.pop("errorMessage", UNSET)

        rag_partition_id = d.pop("ragPartitionId", UNSET)

        cluster_key = d.pop("clusterKey", UNSET)

        file_id = d.pop("fileId", UNSET)

        insert_file_status = cls(
            doc_name=doc_name,
            success=success,
            error_message=error_message,
            rag_partition_id=rag_partition_id,
            cluster_key=cluster_key,
            file_id=file_id,
        )

        insert_file_status.additional_properties = d
        return insert_file_status

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
