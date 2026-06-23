from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from app.domain.value_objects.job_status import JobStatus


@dataclass
class TranslationJob:
    """
    Domain Entity - TranslationJob
    Chứa toàn bộ business logic, không phụ thuộc bất kỳ framework nào.
    """
    original_filename: str
    sender_email: str
    email_uid: str
    status: JobStatus = JobStatus.PENDING

    # Identity
    id: Optional[int] = None

    # Email metadata
    sender_name: str = ""
    subject: str = ""

    # File paths
    original_path: Optional[str] = None
    translated_filename: Optional[str] = None
    translated_path: Optional[str] = None

    # Processing result
    error_message: Optional[str] = None
    char_count: int = 0
    paragraph_count: int = 0

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # ──────────────────────────────────────────────
    # Business Methods (domain logic sống tại đây)
    # ──────────────────────────────────────────────

    def start_processing(self) -> None:
        """Đánh dấu job đang được xử lý."""
        if self.status not in (JobStatus.PENDING, JobStatus.FAILED):
            raise ValueError(f"Không thể chuyển sang PROCESSING từ trạng thái {self.status}")
        self.status = JobStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def complete(
        self,
        translated_filename: str,
        translated_path: str,
        char_count: int,
        paragraph_count: int,
    ) -> None:
        """Đánh dấu job dịch xong thành công."""
        self.status = JobStatus.DONE
        self.translated_filename = translated_filename
        self.translated_path = translated_path
        self.char_count = char_count
        self.paragraph_count = paragraph_count
        now = datetime.utcnow()
        self.completed_at = now
        self.updated_at = now

    def fail(self, error_message: str) -> None:
        """Đánh dấu job thất bại."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def reset_for_retry(self) -> None:
        """Reset job về PENDING để thử lại."""
        if self.status != JobStatus.FAILED:
            raise ValueError("Chỉ có thể retry job ở trạng thái FAILED")
        self.status = JobStatus.PENDING
        self.error_message = None
        self.updated_at = datetime.utcnow()

    @property
    def is_retryable(self) -> bool:
        return self.status == JobStatus.FAILED

    @property
    def display_name(self) -> str:
        return self.sender_name or self.sender_email
