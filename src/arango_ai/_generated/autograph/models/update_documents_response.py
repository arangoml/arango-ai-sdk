from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_file_status import UpdateFileStatus


T = TypeVar("T", bound="UpdateDocumentsResponse")


@_attrs_define
class UpdateDocumentsResponse:
    """UpdateDocumentsResponse is returned immediately when an update starts. The
    delete+insert runs in the background; poll the project-metadata
    importerOrchestration status slot for progress and the terminal outcome.

       Attributes:
           update_id (Union[Unset, str]):
           accepted (Union[Unset, bool]):
           message (Union[Unset, str]):
           results (Union[Unset, list['UpdateFileStatus']]):
    """

    update_id: Union[Unset, str] = UNSET
    accepted: Union[Unset, bool] = UNSET
    message: Union[Unset, str] = UNSET
    results: Union[Unset, list["UpdateFileStatus"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        update_id = self.update_id

        accepted = self.accepted

        message = self.message

        results: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.results, Unset):
            results = []
            for results_item_data in self.results:
                results_item = results_item_data.to_dict()
                results.append(results_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if update_id is not UNSET:
            field_dict["updateId"] = update_id
        if accepted is not UNSET:
            field_dict["accepted"] = accepted
        if message is not UNSET:
            field_dict["message"] = message
        if results is not UNSET:
            field_dict["results"] = results

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.update_file_status import UpdateFileStatus

        d = src_dict.copy()
        update_id = d.pop("updateId", UNSET)

        accepted = d.pop("accepted", UNSET)

        message = d.pop("message", UNSET)

        results = []
        _results = d.pop("results", UNSET)
        for results_item_data in _results or []:
            results_item = UpdateFileStatus.from_dict(results_item_data)

            results.append(results_item)

        update_documents_response = cls(
            update_id=update_id,
            accepted=accepted,
            message=message,
            results=results,
        )

        update_documents_response.additional_properties = d
        return update_documents_response

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
