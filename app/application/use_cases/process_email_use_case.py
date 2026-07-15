"""
Use Case: Poll emails và tạo TranslationJob mới.
Tự động phát hiện ngôn ngữ Nga trong file .docx (không phụ thuộc tên file).
"""
import os
import logging
import hashlib
from app.domain.entities.translation_job import TranslationJob
from app.domain.repositories.job_repository import IJobRepository
from app.application.ports.email_port import IEmailReader
from app.infrastructure.document.language_detector import is_russian_document

logger = logging.getLogger(__name__)


class ProcessEmailUseCase:
    """
    Orchestrate: đọc email mới → lưu file → detect ngôn ngữ → tạo job PENDING.
    Chỉ tạo job cho file .docx có nội dung tiếng Nga.
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
            for attachment in email.attachments:
                # Tránh xử lý file đính kèm đã từng xử lý
                raw_uid = f"{email.uid}:{attachment.filename}"
                attachment_uid = hashlib.sha256(raw_uid.encode('utf-8')).hexdigest()
                
                existing = self._repo.find_by_email_uid(attachment_uid)
                if existing:
                    logger.debug(
                        f"⏩ File '{attachment.filename}' trong Email UID {email.uid} "
                        f"đã được xử lý. Bỏ qua."
                    )
                    continue

                file_path = self._save_file(attachment.filename, attachment.content)

                # Phát hiện ngôn ngữ: chỉ dịch file tiếng Nga
                if not is_russian_document(file_path):
                    logger.info(
                        f"⏩ File '{attachment.filename}' không phải tiếng Nga. "
                        f"Bỏ qua và xóa file tạm."
                    )
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                    continue

                job = TranslationJob(
                    original_filename=attachment.filename,
                    sender_email=email.sender_email,
                    sender_name=email.sender_name,
                    subject=email.subject,
                    email_uid=attachment_uid,
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
