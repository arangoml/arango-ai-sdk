from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.build_strategy import BuildStrategy


T = TypeVar("T", bound="CreateCorpusBuildRequest")


@_attrs_define
class CreateCorpusBuildRequest:
    """CreateCorpusBuildRequest contains parameters for triggering a corpus build.

    Attributes:
        embedding_strategy (Union[Unset, str]):
        strategy (Union[Unset, BuildStrategy]): BuildStrategy contains configurable parameters for corpus build.
        file_ids (Union[Unset, list[str]]):
        modules (Union[Unset, list[str]]):
        incremental (Union[Unset, bool]):
        categories (Union[Unset, list[str]]): field 6 (scope) retired; replaced by categories below.
             Preferred. Category labels resolved via File Manager under GENAI_PROJECT_NAME.
             An already-encoded module label (today's persisted form) is also accepted as a legacy alias.
             Mutually exclusive with modules and file_ids (returns 400 if multiple provided).
             See user_facing_documentation.md §3 for full contract (precedence, default, examples).
    """

    embedding_strategy: Union[Unset, str] = UNSET
    strategy: Union[Unset, "BuildStrategy"] = UNSET
    file_ids: Union[Unset, list[str]] = UNSET
    modules: Union[Unset, list[str]] = UNSET
    incremental: Union[Unset, bool] = UNSET
    categories: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        embedding_strategy = self.embedding_strategy

        strategy: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.strategy, Unset):
            strategy = self.strategy.to_dict()

        file_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.file_ids, Unset):
            file_ids = self.file_ids

        modules: Union[Unset, list[str]] = UNSET
        if not isinstance(self.modules, Unset):
            modules = self.modules

        incremental = self.incremental

        categories: Union[Unset, list[str]] = UNSET
        if not isinstance(self.categories, Unset):
            categories = self.categories

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if embedding_strategy is not UNSET:
            field_dict["embeddingStrategy"] = embedding_strategy
        if strategy is not UNSET:
            field_dict["strategy"] = strategy
        if file_ids is not UNSET:
            field_dict["fileIds"] = file_ids
        if modules is not UNSET:
            field_dict["modules"] = modules
        if incremental is not UNSET:
            field_dict["incremental"] = incremental
        if categories is not UNSET:
            field_dict["categories"] = categories

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.build_strategy import BuildStrategy

        d = src_dict.copy()
        embedding_strategy = d.pop("embeddingStrategy", UNSET)

        _strategy = d.pop("strategy", UNSET)
        strategy: Union[Unset, BuildStrategy]
        if isinstance(_strategy, Unset):
            strategy = UNSET
        else:
            strategy = BuildStrategy.from_dict(_strategy)

        file_ids = cast(list[str], d.pop("fileIds", UNSET))

        modules = cast(list[str], d.pop("modules", UNSET))

        incremental = d.pop("incremental", UNSET)

        categories = cast(list[str], d.pop("categories", UNSET))

        create_corpus_build_request = cls(
            embedding_strategy=embedding_strategy,
            strategy=strategy,
            file_ids=file_ids,
            modules=modules,
            incremental=incremental,
            categories=categories,
        )

        create_corpus_build_request.additional_properties = d
        return create_corpus_build_request

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
