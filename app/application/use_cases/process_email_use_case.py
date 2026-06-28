"""
Use Case: Poll emails và tạo TranslationJob mới.
"""
import os
import logging
from app.domain.entities.translation_job import TranslationJob
from app.domain.repositories.job_repository import IJobRepository
from app.application.ports.email_port import IEmailReader

logger = logging.getLogger(__name__)


class ProcessEmailUseCase:
    """
    Orchestrate: đọc email mới → lưu file → tạo job PENDING.
    Không thực hiện dịch thuật (tách biệt trách nhiệm).
    """

    def __init__(
        self,
        email_reader: IEmailReader,
        job_repository: IJobRepository,
        upload_dir: str,
    ):
        self._reader = email_reader
        self._repo = job_repository
        self._upload_dir = upload_dir

    def execute(self) -> list[TranslationJob]:
        """Quét email mới, tạo job cho từng file hợp lệ. Trả về danh sách job đã tạo."""
        os.makedirs(self._upload_dir, exist_ok=True)
        created_jobs: list[TranslationJob] = []

        emails = self._reader.fetch_unread_with_docx()
        if not emails:
            logger.info("📭 Không có email mới cần xử lý.")
            return []

        for email in emails:
            # Tránh xử lý email đã từng xử lý
            existing = self._repo.find_by_email_uid(email.uid)
            if existing:
                logger.debug(f"⏩ Email UID {email.uid} đã được xử lý. Bỏ qua.")
                continue

            for attachment in email.attachments:
                file_path = self._save_file(attachment.filename, attachment.content)

                job = TranslationJob(
                    original_filename=attachment.filename,
                    sender_email=email.sender_email,
                    sender_name=email.sender_name,
                    subject=email.subject,
                    email_uid=email.uid,
                    original_path=file_path,
                    message_id=email.message_id,
                )
                saved_job = self._repo.save(job)
                created_jobs.append(saved_job)
                logger.info(
                    f"✅ Đã tạo job #{saved_job.id}: {attachment.filename} "
                    f"từ {email.sender_email}"
                )

        return created_jobs

    def _save_file(self, filename: str, content: bytes) -> str:
        """Lưu file và trả về đường dẫn tuyệt đối."""
        file_path = os.path.join(self._upload_dir, filename)
        # Tránh ghi đè
        counter = 1
        base, ext = os.path.splitext(file_path)
        while os.path.exists(file_path):
            file_path = f"{base}_{counter}{ext}"
            counter += 1

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path
