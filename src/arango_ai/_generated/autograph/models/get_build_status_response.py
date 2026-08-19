from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetBuildStatusResponse")


@_attrs_define
class GetBuildStatusResponse:
    """GetBuildStatusResponse contains the current status of a corpus build.

    Attributes:
        corpus_build_id (Union[Unset, str]):
        status (Union[Unset, str]):
        message (Union[Unset, str]):
        progress (Union[Unset, int]):
        error (Union[Unset, str]):
        started_at (Union[Unset, float]):
        completed_at (Union[Unset, float]):
        error_code (Union[Unset, str]):
        graph_name (Union[Unset, str]):
        document_count (Union[Unset, int]):
        cluster_count (Union[Unset, int]):
        documents_added (Union[Unset, int]):
        documents_removed (Union[Unset, int]):
        documents_unchanged (Union[Unset, int]):
    """

    corpus_build_id: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    progress: Union[Unset, int] = UNSET
    error: Union[Unset, str] = UNSET
    started_at: Union[Unset, float] = UNSET
    completed_at: Union[Unset, float] = UNSET
    error_code: Union[Unset, str] = UNSET
    graph_name: Union[Unset, str] = UNSET
    document_count: Union[Unset, int] = UNSET
    cluster_count: Union[Unset, int] = UNSET
    documents_added: Union[Unset, int] = UNSET
    documents_removed: Union[Unset, int] = UNSET
    documents_unchanged: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        corpus_build_id = self.corpus_build_id

        status = self.status

        message = self.message

        progress = self.progress

        error = self.error

        started_at = self.started_at

        completed_at = self.completed_at

        error_code = self.error_code

        graph_name = self.graph_name

        document_count = self.document_count

        cluster_count = self.cluster_count

        documents_added = self.documents_added

        documents_removed = self.documents_removed

        documents_unchanged = self.documents_unchanged

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if corpus_build_id is not UNSET:
            field_dict["corpusBuildId"] = corpus_build_id
        if status is not UNSET:
            field_dict["status"] = status
        if message is not UNSET:
            field_dict["message"] = message
        if progress is not UNSET:
            field_dict["progress"] = progress
        if error is not UNSET:
            field_dict["error"] = error
        if started_at is not UNSET:
            field_dict["startedAt"] = started_at
        if completed_at is not UNSET:
            field_dict["completedAt"] = completed_at
        if error_code is not UNSET:
            field_dict["errorCode"] = error_code
        if graph_name is not UNSET:
            field_dict["graphName"] = graph_name
        if document_count is not UNSET:
            field_dict["documentCount"] = document_count
        if cluster_count is not UNSET:
            field_dict["clusterCount"] = cluster_count
        if documents_added is not UNSET:
            field_dict["documentsAdded"] = documents_added
        if documents_removed is not UNSET:
            field_dict["documentsRemoved"] = documents_removed
        if documents_unchanged is not UNSET:
            field_dict["documentsUnchanged"] = documents_unchanged

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        corpus_build_id = d.pop("corpusBuildId", UNSET)

        status = d.pop("status", UNSET)

        message = d.pop("message", UNSET)

        progress = d.pop("progress", UNSET)

        error = d.pop("error", UNSET)

        started_at = d.pop("startedAt", UNSET)

        completed_at = d.pop("completedAt", UNSET)

        error_code = d.pop("errorCode", UNSET)

        graph_name = d.pop("graphName", UNSET)

        document_count = d.pop("documentCount", UNSET)

        cluster_count = d.pop("clusterCount", UNSET)

        documents_added = d.pop("documentsAdded", UNSET)

        documents_removed = d.pop("documentsRemoved", UNSET)

        documents_unchanged = d.pop("documentsUnchanged", UNSET)

        get_build_status_response = cls(
            corpus_build_id=corpus_build_id,
            status=status,
            message=message,
            progress=progress,
            error=error,
            started_at=started_at,
            completed_at=completed_at,
            error_code=error_code,
            graph_name=graph_name,
            document_count=document_count,
            cluster_count=cluster_count,
            documents_added=documents_added,
            documents_removed=documents_removed,
            documents_unchanged=documents_unchanged,
        )

        get_build_status_response.additional_properties = d
        return get_build_status_response

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
