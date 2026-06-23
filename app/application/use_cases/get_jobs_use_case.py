"""
Use Case: Lấy danh sách và thống kê jobs (dùng cho dashboard).
"""
from dataclasses import dataclass
from app.domain.entities.translation_job import TranslationJob
from app.domain.repositories.job_repository import IJobRepository
from app.domain.value_objects.job_status import JobStatus


@dataclass
class JobStats:
    total: int
    pending: int
    processing: int
    done: int
    failed: int


class GetJobsUseCase:

    def __init__(self, job_repository: IJobRepository):
        self._repo = job_repository

    def get_all(self, limit: int = 100, offset: int = 0) -> list[TranslationJob]:
        return self._repo.find_all(limit=limit, offset=offset)

    def get_by_id(self, job_id: int) -> TranslationJob | None:
        return self._repo.find_by_id(job_id)

    def get_stats(self) -> JobStats:
        return JobStats(
            total=sum([
                self._repo.count_by_status(s) for s in JobStatus
            ]),
            pending=self._repo.count_by_status(JobStatus.PENDING),
            processing=self._repo.count_by_status(JobStatus.PROCESSING),
            done=self._repo.count_by_status(JobStatus.DONE),
            failed=self._repo.count_by_status(JobStatus.FAILED),
        )
