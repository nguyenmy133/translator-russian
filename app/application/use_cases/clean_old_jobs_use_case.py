"""
Use Case: Tự động dọn dẹp các jobs và file tương ứng đã quá 1 tuần.
"""
import os
import logging
from app.domain.repositories.job_repository import IJobRepository

logger = logging.getLogger(__name__)


class CleanOldJobsUseCase:

    def __init__(self, job_repository: IJobRepository):
        self._repo = job_repository

    def execute(self, days: int = 7) -> int:
        """Xóa các job cũ hơn số ngày chỉ định. Trả về số job đã xóa."""
        old_jobs = self._repo.find_older_than_days(days)
        if not old_jobs:
            return 0

        logger.info(f"🧹 Bắt đầu dọn dẹp {len(old_jobs)} bài dịch cũ hơn {days} ngày...")
        deleted_count = 0
        for job in old_jobs:
            # 1. Xóa file gốc trên đĩa
            if job.original_path and os.path.exists(job.original_path):
                try:
                    os.remove(job.original_path)
                    logger.debug(f"Đã xóa file gốc: {job.original_path}")
                except Exception as e:
                    logger.error(f"Lỗi xóa file gốc {job.original_path}: {e}")

            # 2. Xóa file đã dịch trên đĩa
            if job.translated_path and os.path.exists(job.translated_path):
                try:
                    os.remove(job.translated_path)
                    logger.debug(f"Đã xóa file dịch: {job.translated_path}")
                except Exception as e:
                    logger.error(f"Lỗi xóa file dịch {job.translated_path}: {e}")

            # 3. Xóa bản ghi trong database
            try:
                self._repo.delete(job.id)
                deleted_count += 1
                logger.info(f"Đã xóa job #{job.id} ({job.original_filename})")
            except Exception as e:
                logger.error(f"Lỗi xóa job #{job.id} trong DB: {e}")

        return deleted_count
