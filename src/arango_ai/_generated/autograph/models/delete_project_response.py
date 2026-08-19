from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Union


T = TypeVar("T", bound="DeleteProjectResponse")


@_attrs_define
class DeleteProjectResponse:
    """DeleteProjectResponse reports every resource removed by the synchronous
    cleanup. deleted=false and warnings describe a retryable partial failure.

       Attributes:
           deleted (Union[Unset, bool]):
           project (Union[Unset, str]):
           collections_deleted (Union[Unset, list[str]]):
           graphs_deleted (Union[Unset, list[str]]):
           services_deleted (Union[Unset, list[str]]):
           files_deleted (Union[Unset, int]):
           locked_skipped (Union[Unset, list[str]]):
           warnings (Union[Unset, list[str]]):
           views_deleted (Union[Unset, list[str]]):
    """

    deleted: Union[Unset, bool] = UNSET
    project: Union[Unset, str] = UNSET
    collections_deleted: Union[Unset, list[str]] = UNSET
    graphs_deleted: Union[Unset, list[str]] = UNSET
    services_deleted: Union[Unset, list[str]] = UNSET
    files_deleted: Union[Unset, int] = UNSET
    locked_skipped: Union[Unset, list[str]] = UNSET
    warnings: Union[Unset, list[str]] = UNSET
    views_deleted: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deleted = self.deleted

        project = self.project

        collections_deleted: Union[Unset, list[str]] = UNSET
        if not isinstance(self.collections_deleted, Unset):
            collections_deleted = self.collections_deleted

        graphs_deleted: Union[Unset, list[str]] = UNSET
        if not isinstance(self.graphs_deleted, Unset):
            graphs_deleted = self.graphs_deleted

        services_deleted: Union[Unset, list[str]] = UNSET
        if not isinstance(self.services_deleted, Unset):
            services_deleted = self.services_deleted

        files_deleted = self.files_deleted

        locked_skipped: Union[Unset, list[str]] = UNSET
        if not isinstance(self.locked_skipped, Unset):
            locked_skipped = self.locked_skipped

        warnings: Union[Unset, list[str]] = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = self.warnings

        views_deleted: Union[Unset, list[str]] = UNSET
        if not isinstance(self.views_deleted, Unset):
            views_deleted = self.views_deleted

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if project is not UNSET:
            field_dict["project"] = project
        if collections_deleted is not UNSET:
            field_dict["collectionsDeleted"] = collections_deleted
        if graphs_deleted is not UNSET:
            field_dict["graphsDeleted"] = graphs_deleted
        if services_deleted is not UNSET:
            field_dict["servicesDeleted"] = services_deleted
        if files_deleted is not UNSET:
            field_dict["filesDeleted"] = files_deleted
        if locked_skipped is not UNSET:
            field_dict["lockedSkipped"] = locked_skipped
        if warnings is not UNSET:
            field_dict["warnings"] = warnings
        if views_deleted is not UNSET:
            field_dict["viewsDeleted"] = views_deleted

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        deleted = d.pop("deleted", UNSET)

        project = d.pop("project", UNSET)

        collections_deleted = cast(list[str], d.pop("collectionsDeleted", UNSET))

        graphs_deleted = cast(list[str], d.pop("graphsDeleted", UNSET))

        services_deleted = cast(list[str], d.pop("servicesDeleted", UNSET))

        files_deleted = d.pop("filesDeleted", UNSET)

        locked_skipped = cast(list[str], d.pop("lockedSkipped", UNSET))

        warnings = cast(list[str], d.pop("warnings", UNSET))

        views_deleted = cast(list[str], d.pop("viewsDeleted", UNSET))

        delete_project_response = cls(
            deleted=deleted,
            project=project,
            collections_deleted=collections_deleted,
            graphs_deleted=graphs_deleted,
            services_deleted=services_deleted,
            files_deleted=files_deleted,
            locked_skipped=locked_skipped,
            warnings=warnings,
            views_deleted=views_deleted,
        )

        delete_project_response.additional_properties = d
        return delete_project_response

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
