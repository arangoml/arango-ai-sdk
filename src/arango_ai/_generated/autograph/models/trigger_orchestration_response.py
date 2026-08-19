from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.orchestration_job_result import OrchestrationJobResult


T = TypeVar("T", bound="TriggerOrchestrationResponse")


@_attrs_define
class TriggerOrchestrationResponse:
    """TriggerOrchestrationResponse is returned immediately when orchestration starts.

    Attributes:
        orchestration_id (Union[Unset, str]):
        success (Union[Unset, bool]):
        message (Union[Unset, str]):
        total_jobs (Union[Unset, int]):
        completed_jobs (Union[Unset, int]):
        failed_jobs (Union[Unset, int]):
        job_results (Union[Unset, list['OrchestrationJobResult']]):
        unmatched_file_ids (Union[Unset, list[str]]):
    """

    orchestration_id: Union[Unset, str] = UNSET
    success: Union[Unset, bool] = UNSET
    message: Union[Unset, str] = UNSET
    total_jobs: Union[Unset, int] = UNSET
    completed_jobs: Union[Unset, int] = UNSET
    failed_jobs: Union[Unset, int] = UNSET
    job_results: Union[Unset, list["OrchestrationJobResult"]] = UNSET
    unmatched_file_ids: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        orchestration_id = self.orchestration_id

        success = self.success

        message = self.message

        total_jobs = self.total_jobs

        completed_jobs = self.completed_jobs

        failed_jobs = self.failed_jobs

        job_results: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.job_results, Unset):
            job_results = []
            for job_results_item_data in self.job_results:
                job_results_item = job_results_item_data.to_dict()
                job_results.append(job_results_item)

        unmatched_file_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.unmatched_file_ids, Unset):
            unmatched_file_ids = self.unmatched_file_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if orchestration_id is not UNSET:
            field_dict["orchestrationId"] = orchestration_id
        if success is not UNSET:
            field_dict["success"] = success
        if message is not UNSET:
            field_dict["message"] = message
        if total_jobs is not UNSET:
            field_dict["totalJobs"] = total_jobs
        if completed_jobs is not UNSET:
            field_dict["completedJobs"] = completed_jobs
        if failed_jobs is not UNSET:
            field_dict["failedJobs"] = failed_jobs
        if job_results is not UNSET:
            field_dict["jobResults"] = job_results
        if unmatched_file_ids is not UNSET:
            field_dict["unmatchedFileIds"] = unmatched_file_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.orchestration_job_result import OrchestrationJobResult

        d = src_dict.copy()
        orchestration_id = d.pop("orchestrationId", UNSET)

        success = d.pop("success", UNSET)

        message = d.pop("message", UNSET)

        total_jobs = d.pop("totalJobs", UNSET)

        completed_jobs = d.pop("completedJobs", UNSET)

        failed_jobs = d.pop("failedJobs", UNSET)

        job_results = []
        _job_results = d.pop("jobResults", UNSET)
        for job_results_item_data in _job_results or []:
            job_results_item = OrchestrationJobResult.from_dict(job_results_item_data)

            job_results.append(job_results_item)

        unmatched_file_ids = cast(list[str], d.pop("unmatchedFileIds", UNSET))

        trigger_orchestration_response = cls(
            orchestration_id=orchestration_id,
            success=success,
            message=message,
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            job_results=job_results,
            unmatched_file_ids=unmatched_file_ids,
        )

        trigger_orchestration_response.additional_properties = d
        return trigger_orchestration_response

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
