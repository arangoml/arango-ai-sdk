from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CorpusGraphOverview")


@_attrs_define
class CorpusGraphOverview:
    """CorpusGraphOverview describes the corpus graph card on the Overview page.

    Attributes:
        name (Union[Unset, str]):
        status (Union[Unset, str]):
        document_count (Union[Unset, int]):
        cluster_count (Union[Unset, int]):
        stale (Union[Unset, bool]):
        graph_explorer_url (Union[Unset, str]):
    """

    name: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    document_count: Union[Unset, int] = UNSET
    cluster_count: Union[Unset, int] = UNSET
    stale: Union[Unset, bool] = UNSET
    graph_explorer_url: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        status = self.status

        document_count = self.document_count

        cluster_count = self.cluster_count

        stale = self.stale

        graph_explorer_url = self.graph_explorer_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if status is not UNSET:
            field_dict["status"] = status
        if document_count is not UNSET:
            field_dict["documentCount"] = document_count
        if cluster_count is not UNSET:
            field_dict["clusterCount"] = cluster_count
        if stale is not UNSET:
            field_dict["stale"] = stale
        if graph_explorer_url is not UNSET:
            field_dict["graphExplorerUrl"] = graph_explorer_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        status = d.pop("status", UNSET)

        document_count = d.pop("documentCount", UNSET)

        cluster_count = d.pop("clusterCount", UNSET)

        stale = d.pop("stale", UNSET)

        graph_explorer_url = d.pop("graphExplorerUrl", UNSET)

        corpus_graph_overview = cls(
            name=name,
            status=status,
            document_count=document_count,
            cluster_count=cluster_count,
            stale=stale,
            graph_explorer_url=graph_explorer_url,
        )

        corpus_graph_overview.additional_properties = d
        return corpus_graph_overview

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
