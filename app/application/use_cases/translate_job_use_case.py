"""
Use Case: Dịch file Word cho một TranslationJob.
"""
import os
import re
import logging
from app.domain.repositories.job_repository import IJobRepository
from app.domain.value_objects.job_status import JobStatus
from app.application.ports.translator_port import ITranslator
from app.application.ports.document_port import IDocumentParser
from app.application.ports.email_port import IEmailSender

logger = logging.getLogger(__name__)


def _rename_ru_to_vi(filename: str) -> str:
    """
    Đổi tên file từ dạng tiếng Nga sang tiếng Việt. Hỗ trợ các format:

      Format thực tế:
        "23.06 GBPUSD ru.docx"  →  "23.06 GBPUSD (vi).docx"
        (space + ru trước .docx, KHÔNG ngoặc → thêm ngoặc vào vi)

      Format có ngoặc:
        "abc (ru).docx"         →  "abc (vi).docx"
        "abc(ru).docx"          →  "abc(vi).docx"
    """
    # Pattern 1 — format THỰC TẾ: " ru.docx" → " (vi).docx"
    result = re.sub(r'\s+ru\.docx$', ' (vi).docx', filename, flags=re.IGNORECASE)
    if result != filename:
        return result

    # Pattern 2 — format có ngoặc: "(ru)" → "(vi)"
    result = re.sub(r'\(ru\)', '(vi)', filename, flags=re.IGNORECASE)
    if result != filename:
        return result

    # Fallback — không khớp pattern nào: thêm (vi) trước extension
    name, ext = os.path.splitext(filename)
    return f"{name} (vi){ext}"


class TranslateJobUseCase:
    """
    Orchestrate: lấy job PENDING → dịch file → cập nhật job → gửi email kết quả.
    """

    def __init__(
        self,
        job_repository: IJobRepository,
        translator: ITranslator,
        document_parser: IDocumentParser,
        email_sender: IEmailSender,
        output_dir: str,
        translator_email: str,
    ):
        self._repo = job_repository
        self._translator = translator
        self._parser = document_parser
        self._sender = email_sender
        self._output_dir = output_dir
        self._translator_email = translator_email

    def execute_pending(self) -> int:
        """Xử lý tất cả job đang PENDING. Trả về số job đã xử lý."""
        pending_jobs = self._repo.find_by_status(JobStatus.PENDING)
        if not pending_jobs:
            return 0

        logger.info(f"🔄 Bắt đầu xử lý {len(pending_jobs)} job đang chờ...")
        processed = 0
        for job in pending_jobs:
            self.execute_single(job.id)
            processed += 1

        return processed

    def execute_single(self, job_id: int) -> None:
        """Dịch một job cụ thể theo ID."""
        job = self._repo.find_by_id(job_id)
        if not job:
            logger.error(f"❌ Không tìm thấy job #{job_id}")
            return

        if job.status not in (JobStatus.PENDING, JobStatus.FAILED):
            logger.warning(f"⚠️ Job #{job_id} đang ở trạng thái {job.status}. Bỏ qua.")
            return

        # 1. Đánh dấu đang xử lý
        job.start_processing()
        self._repo.save(job)

        os.makedirs(self._output_dir, exist_ok=True)
        translated_filename = _rename_ru_to_vi(job.original_filename)
        output_path = os.path.join(self._output_dir, translated_filename)

        try:
            # 2. Dịch file
            logger.info(f"🌐 Đang dịch: {job.original_filename} → {translated_filename}")
            stats = self._parser.translate_and_save(
                input_path=job.original_path,
                output_path=output_path,
                translate_fn=self._translator.translate,
            )

            # 3. Cập nhật entity (domain logic)
            job.complete(
                translated_filename=translated_filename,
                translated_path=output_path,
                char_count=stats.char_count,
                paragraph_count=stats.paragraph_count,
            )
            self._repo.save(job)

            # 4. Gửi email kết quả
            # Gửi cho người gửi gốc (khách hàng) - chỉ gửi file
            self._sender.send_success(
                to_email=job.sender_email,
                to_name=job.sender_name,
                original_filename=job.original_filename,
                translated_file_path=output_path,
                translated_filename=translated_filename,
                paragraph_count=stats.paragraph_count,
                char_count=stats.char_count,
                file_only=True,
                original_message_id=job.message_id,
                original_subject=job.subject,
            )
            # Gửi thông báo cho người dịch (chủ hệ thống) - chỉ gửi nếu khác email khách hàng
            if self._translator_email and job.sender_email.lower().strip() != self._translator_email.lower().strip():
                self._sender.send_success(
                    to_email=self._translator_email,
                    to_name=job.sender_name,
                    original_filename=job.original_filename,
                    translated_file_path=output_path,
                    translated_filename=translated_filename,
                    paragraph_count=stats.paragraph_count,
                    char_count=stats.char_count,
                    original_message_id=job.message_id,
                    original_subject=job.subject,
                )
            logger.info(f"✅ Job #{job_id} hoàn thành. Đã gửi cho khách hàng ({job.sender_email}) và người dịch ({self._translator_email})")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Job #{job_id} thất bại: {error_msg}")

            job.fail(error_message=error_msg)
            self._repo.save(job)

            # Gửi email thông báo lỗi
            try:
                self._sender.send_failure(
                    to_email=job.sender_email,
                    original_filename=job.original_filename,
                    error=error_msg,
                    original_message_id=job.message_id,
                )
            except Exception as send_err:
                logger.error(f"Không thể gửi email lỗi: {send_err}")
