"""
Use Case: Lấy danh sách và thống kê jobs (dùng cho dashboard).
Hỗ trợ xóa hàng loạt jobs kèm file trên disk.
"""
import os
import logging
from dataclasses import dataclass
from app.domain.entities.translation_job import TranslationJob
from app.domain.repositories.job_repository import IJobRepository
from app.domain.value_objects.job_status import JobStatus

logger = logging.getLogger(__name__)


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

    def delete_jobs(self, job_ids: list[int]) -> int:
        """Xóa nhiều jobs theo IDs, đồng thời dọn file trên disk."""
        # Lấy thông tin job trước khi xóa để dọn file
        for job_id in job_ids:
            job = self._repo.find_by_id(job_id)
            if job:
                # Xóa file gốc
                if job.original_path and os.path.exists(job.original_path):
                    try:
                        os.remove(job.original_path)
                        logger.info(f"🗑️ Đã xóa file gốc: {job.original_path}")
                    except OSError as e:
                        logger.warning(f"⚠️ Không xóa được file gốc: {e}")
                # Xóa file đã dịch
                if job.translated_path and os.path.exists(job.translated_path):
                    try:
                        os.remove(job.translated_path)
                        logger.info(f"🗑️ Đã xóa file dịch: {job.translated_path}")
                    except OSError as e:
                        logger.warning(f"⚠️ Không xóa được file dịch: {e}")

        # Xóa records trong DB
        deleted = self._repo.delete_by_ids(job_ids)
        logger.info(f"🗑️ Đã xóa {deleted} jobs từ database")
        return deleted
