"""
Use Case: Retry một job FAILED.
"""
import logging
from app.domain.repositories.job_repository import IJobRepository
from app.application.use_cases.translate_job_use_case import TranslateJobUseCase

logger = logging.getLogger(__name__)


class RetryJobUseCase:

    def __init__(
        self,
        job_repository: IJobRepository,
        translate_job_use_case: TranslateJobUseCase,
    ):
        self._repo = job_repository
        self._translate_uc = translate_job_use_case

    def execute(self, job_id: int) -> None:
        job = self._repo.find_by_id(job_id)
        if not job:
            raise ValueError(f"Job #{job_id} không tồn tại")

        # Domain entity validate trạng thái hợp lệ
        job.reset_for_retry()
        self._repo.save(job)

        logger.info(f"🔁 Job #{job_id} đã được reset để retry.")

        # Thực hiện dịch lại ngay lập tức
        self._translate_uc.execute_single(job_id)
