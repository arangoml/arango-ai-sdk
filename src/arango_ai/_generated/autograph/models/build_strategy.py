from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union

if TYPE_CHECKING:
    from ..models.build_strategy_custom_params import BuildStrategyCustomParams


T = TypeVar("T", bound="BuildStrategy")


@_attrs_define
class BuildStrategy:
    """BuildStrategy contains configurable parameters for corpus build.

    Attributes:
        top_k (Union[Unset, int]):
        cluster_threshold (Union[Unset, int]):
        custom_params (Union[Unset, BuildStrategyCustomParams]):
    """

    top_k: Union[Unset, int] = UNSET
    cluster_threshold: Union[Unset, int] = UNSET
    custom_params: Union[Unset, "BuildStrategyCustomParams"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        top_k = self.top_k

        cluster_threshold = self.cluster_threshold

        custom_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.custom_params, Unset):
            custom_params = self.custom_params.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if top_k is not UNSET:
            field_dict["topK"] = top_k
        if cluster_threshold is not UNSET:
            field_dict["clusterThreshold"] = cluster_threshold
        if custom_params is not UNSET:
            field_dict["customParams"] = custom_params

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.build_strategy_custom_params import BuildStrategyCustomParams

        d = src_dict.copy()
        top_k = d.pop("topK", UNSET)

        cluster_threshold = d.pop("clusterThreshold", UNSET)

        _custom_params = d.pop("customParams", UNSET)
        custom_params: Union[Unset, BuildStrategyCustomParams]
        if isinstance(_custom_params, Unset):
            custom_params = UNSET
        else:
            custom_params = BuildStrategyCustomParams.from_dict(_custom_params)

        build_strategy = cls(
            top_k=top_k,
            cluster_threshold=cluster_threshold,
            custom_params=custom_params,
        )

        build_strategy.additional_properties = d
        return build_strategy

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
