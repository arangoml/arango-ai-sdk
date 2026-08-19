from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.orchestration_job_result import OrchestrationJobResult


T = TypeVar("T", bound="GetOrchestrationStatusResponse")


@_attrs_define
class GetOrchestrationStatusResponse:
    """GetOrchestrationStatusResponse returns the live or final status of an orchestration run.

    Attributes:
        orchestration_id (Union[Unset, str]):
        status (Union[Unset, str]):
        total_jobs (Union[Unset, int]):
        completed_jobs (Union[Unset, int]):
        failed_jobs (Union[Unset, int]):
        message (Union[Unset, str]):
        jobs (Union[Unset, list['OrchestrationJobResult']]):
    """

    orchestration_id: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    total_jobs: Union[Unset, int] = UNSET
    completed_jobs: Union[Unset, int] = UNSET
    failed_jobs: Union[Unset, int] = UNSET
    message: Union[Unset, str] = UNSET
    jobs: Union[Unset, list["OrchestrationJobResult"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        orchestration_id = self.orchestration_id

        status = self.status

        total_jobs = self.total_jobs

        completed_jobs = self.completed_jobs

        failed_jobs = self.failed_jobs

        message = self.message

        jobs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.jobs, Unset):
            jobs = []
            for jobs_item_data in self.jobs:
                jobs_item = jobs_item_data.to_dict()
                jobs.append(jobs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if orchestration_id is not UNSET:
            field_dict["orchestrationId"] = orchestration_id
        if status is not UNSET:
            field_dict["status"] = status
        if total_jobs is not UNSET:
            field_dict["totalJobs"] = total_jobs
        if completed_jobs is not UNSET:
            field_dict["completedJobs"] = completed_jobs
        if failed_jobs is not UNSET:
            field_dict["failedJobs"] = failed_jobs
        if message is not UNSET:
            field_dict["message"] = message
        if jobs is not UNSET:
            field_dict["jobs"] = jobs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.orchestration_job_result import OrchestrationJobResult

        d = src_dict.copy()
        orchestration_id = d.pop("orchestrationId", UNSET)

        status = d.pop("status", UNSET)

        total_jobs = d.pop("totalJobs", UNSET)

        completed_jobs = d.pop("completedJobs", UNSET)

        failed_jobs = d.pop("failedJobs", UNSET)

        message = d.pop("message", UNSET)

        jobs = []
        _jobs = d.pop("jobs", UNSET)
        for jobs_item_data in _jobs or []:
            jobs_item = OrchestrationJobResult.from_dict(jobs_item_data)

            jobs.append(jobs_item)

        get_orchestration_status_response = cls(
            orchestration_id=orchestration_id,
            status=status,
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            message=message,
            jobs=jobs,
        )

        get_orchestration_status_response.additional_properties = d
        return get_orchestration_status_response

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
