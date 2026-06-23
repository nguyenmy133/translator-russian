"""
Domain Repository Interface (Port)
Định nghĩa contract thuần túy — infrastructure phải implement.
"""
from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.translation_job import TranslationJob
from app.domain.value_objects.job_status import JobStatus


class IJobRepository(ABC):

    @abstractmethod
    def save(self, job: TranslationJob) -> TranslationJob:
        """Tạo mới hoặc cập nhật job. Trả về job với id được gán."""
        ...

    @abstractmethod
    def find_by_id(self, job_id: int) -> Optional[TranslationJob]:
        ...

    @abstractmethod
    def find_by_email_uid(self, email_uid: str) -> Optional[TranslationJob]:
        """Tìm job theo UID email, tránh xử lý trùng lặp."""
        ...

    @abstractmethod
    def find_by_status(self, status: JobStatus) -> list[TranslationJob]:
        ...

    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> list[TranslationJob]:
        ...

    @abstractmethod
    def count_by_status(self, status: JobStatus) -> int:
        ...
