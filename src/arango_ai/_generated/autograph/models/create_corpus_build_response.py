from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateCorpusBuildResponse")


@_attrs_define
class CreateCorpusBuildResponse:
    """CreateCorpusBuildResponse contains the corpus build ID.

    Attributes:
        corpus_build_id (Union[Unset, str]):
        graph_name (Union[Unset, str]):
    """

    corpus_build_id: Union[Unset, str] = UNSET
    graph_name: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        corpus_build_id = self.corpus_build_id

        graph_name = self.graph_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if corpus_build_id is not UNSET:
            field_dict["corpusBuildId"] = corpus_build_id
        if graph_name is not UNSET:
            field_dict["graphName"] = graph_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        corpus_build_id = d.pop("corpusBuildId", UNSET)

        graph_name = d.pop("graphName", UNSET)

        create_corpus_build_response = cls(
            corpus_build_id=corpus_build_id,
            graph_name=graph_name,
        )

        create_corpus_build_response.additional_properties = d
        return create_corpus_build_response

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
