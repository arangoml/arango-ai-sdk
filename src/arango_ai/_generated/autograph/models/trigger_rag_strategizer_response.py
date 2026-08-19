from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TriggerRAGStrategizerResponse")


@_attrs_define
class TriggerRAGStrategizerResponse:
    """TriggerRAGStrategizerResponse is returned when the strategizer job is accepted.
    Results are stored in rags collection and can be queried from the database.

       Attributes:
           strategize_job_id (Union[Unset, str]):
    """

    strategize_job_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        strategize_job_id = self.strategize_job_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if strategize_job_id is not UNSET:
            field_dict["strategizeJobId"] = strategize_job_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        strategize_job_id = d.pop("strategizeJobId", UNSET)

        trigger_rag_strategizer_response = cls(
            strategize_job_id=strategize_job_id,
        )

        trigger_rag_strategizer_response.additional_properties = d
        return trigger_rag_strategizer_response

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
