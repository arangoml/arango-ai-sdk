from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.trigger_rag_strategizer_request_complexity import (
    TriggerRAGStrategizerRequestComplexity,
)
from typing import cast
from typing import Union


T = TypeVar("T", bound="TriggerRAGStrategizerRequest")


@_attrs_define
class TriggerRAGStrategizerRequest:
    """TriggerRAGStrategizerRequest contains parameters for RAG strategy analysis.

    Attributes:
        project (Union[Unset, str]):
        complexity (Union[Unset, TriggerRAGStrategizerRequestComplexity]):
        extract_images_default (Union[Unset, bool]):
        categories (Union[Unset, list[str]]):
        max_parallel_clusters (Union[Unset, int]):
    """

    project: Union[Unset, str] = UNSET
    complexity: Union[Unset, TriggerRAGStrategizerRequestComplexity] = UNSET
    extract_images_default: Union[Unset, bool] = UNSET
    categories: Union[Unset, list[str]] = UNSET
    max_parallel_clusters: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project = self.project

        complexity: Union[Unset, str] = UNSET
        if not isinstance(self.complexity, Unset):
            complexity = self.complexity.value

        extract_images_default = self.extract_images_default

        categories: Union[Unset, list[str]] = UNSET
        if not isinstance(self.categories, Unset):
            categories = self.categories

        max_parallel_clusters = self.max_parallel_clusters

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project is not UNSET:
            field_dict["project"] = project
        if complexity is not UNSET:
            field_dict["complexity"] = complexity
        if extract_images_default is not UNSET:
            field_dict["extractImagesDefault"] = extract_images_default
        if categories is not UNSET:
            field_dict["categories"] = categories
        if max_parallel_clusters is not UNSET:
            field_dict["maxParallelClusters"] = max_parallel_clusters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        project = d.pop("project", UNSET)

        _complexity = d.pop("complexity", UNSET)
        complexity: Union[Unset, TriggerRAGStrategizerRequestComplexity]
        if isinstance(_complexity, Unset):
            complexity = UNSET
        else:
            complexity = TriggerRAGStrategizerRequestComplexity(_complexity)

        extract_images_default = d.pop("extractImagesDefault", UNSET)

        categories = cast(list[str], d.pop("categories", UNSET))

        max_parallel_clusters = d.pop("maxParallelClusters", UNSET)

        trigger_rag_strategizer_request = cls(
            project=project,
            complexity=complexity,
            extract_images_default=extract_images_default,
            categories=categories,
            max_parallel_clusters=max_parallel_clusters,
        )

        trigger_rag_strategizer_request.additional_properties = d
        return trigger_rag_strategizer_request

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
