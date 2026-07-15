"""
Dependency Injection Container
Wires all layers together — đây là nơi duy nhất biết về tất cả các class cụ thể.
"""
import logging
from functools import lru_cache
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from core.encryption import decrypt_password
from app.infrastructure.persistence.database import create_db_engine, create_session_factory, Base
from app.infrastructure.persistence.orm_models import TranslationJobORM  # noqa: trigger metadata
from app.infrastructure.persistence.email_account_orm import EmailAccountORM  # noqa: trigger metadata
from app.infrastructure.persistence.job_repository_impl import SQLiteJobRepository
from app.infrastructure.persistence.email_account_repository import EmailAccountRepository
from app.infrastructure.email.gmail_reader import GmailIMAPReader
from app.infrastructure.email.gmail_sender import GmailSMTPSender
from app.infrastructure.translation.gemini_translator import GeminiTranslatorAdapter
from app.infrastructure.translation.google_translator import GoogleTranslatorAdapter
from app.infrastructure.translation.fallback_translator import FallbackTranslator
from app.infrastructure.document.docx_parser import DocxParser

from app.application.use_cases.process_email_use_case import ProcessEmailUseCase
from app.application.use_cases.translate_job_use_case import TranslateJobUseCase
from app.application.use_cases.retry_job_use_case import RetryJobUseCase
from app.application.use_cases.get_jobs_use_case import GetJobsUseCase
from app.application.use_cases.clean_old_jobs_use_case import CleanOldJobsUseCase

logger = logging.getLogger(__name__)

# ── Singletons ──────────────────────────────────────────────────────

_settings = get_settings()
_engine = create_db_engine(_settings.database_url)
_session_factory = create_session_factory(_engine)


def init_database():
    """Tạo bảng nếu chưa có. Gọi khi khởi động app."""
    Base.metadata.create_all(bind=_engine)


# ── Factory functions ────────────────────────────────────────────────

def get_job_repository() -> SQLiteJobRepository:
    return SQLiteJobRepository(_session_factory)


def get_email_account_repository() -> EmailAccountRepository:
    return EmailAccountRepository(_session_factory)


def _get_email_credentials() -> tuple[str, str, str, int, str, int]:
    """
    Lấy email credentials từ DB (ưu tiên) hoặc .env (fallback).
    Trả về: (email, password, imap_host, imap_port, smtp_host, smtp_port)
    """
    repo = get_email_account_repository()
    account = repo.get_active()

    if account and account.app_password_encrypted:
        try:
            password = decrypt_password(
                account.app_password_encrypted, _settings.secret_key
            )
            logger.debug(f"📧 Sử dụng email từ DB: {account.email_address}")
            return (
                account.email_address,
                password,
                account.imap_host or _settings.imap_host,
                account.imap_port or _settings.imap_port,
                account.smtp_host or _settings.smtp_host,
                account.smtp_port or _settings.smtp_port,
            )
        except Exception as e:
            logger.warning(f"⚠️ Không giải mã được password từ DB: {e}. Fallback .env")

    # Fallback: dùng .env
    logger.debug("📧 Sử dụng email từ .env (fallback)")
    return (
        _settings.gmail_address,
        _settings.gmail_app_password,
        _settings.imap_host,
        _settings.imap_port,
        _settings.smtp_host,
        _settings.smtp_port,
    )


def get_email_reader() -> GmailIMAPReader:
    email, password, imap_host, imap_port, _, _ = _get_email_credentials()
    return GmailIMAPReader(
        host=imap_host,
        port=imap_port,
        email_address=email,
        app_password=password,
        allowed_senders=_settings.allowed_senders,
    )


def get_email_sender() -> GmailSMTPSender:
    email, password, _, _, smtp_host, smtp_port = _get_email_credentials()
    return GmailSMTPSender(
        host=smtp_host,
        port=smtp_port,
        email_address=email,
        app_password=password,
    )


def get_translator() -> FallbackTranslator:
    primary = GeminiTranslatorAdapter(
        api_key=_settings.gemini_api_key,
        source="ru",
        target="vi",
    )
    fallback = GoogleTranslatorAdapter(
        source="ru",
        target="vi",
    )
    return FallbackTranslator(primary=primary, fallback=fallback)


def get_document_parser() -> DocxParser:
    return DocxParser()


# ── Use Case factories ───────────────────────────────────────────────

def get_process_email_use_case() -> ProcessEmailUseCase:
    return ProcessEmailUseCase(
        email_reader=get_email_reader(),
        job_repository=get_job_repository(),
        upload_dir=_settings.upload_dir,
    )


def get_translate_job_use_case() -> TranslateJobUseCase:
    email, _, _, _, _, _ = _get_email_credentials()
    return TranslateJobUseCase(
        job_repository=get_job_repository(),
        translator=get_translator(),
        document_parser=get_document_parser(),
        email_sender=get_email_sender(),
        output_dir=_settings.output_dir,
        translator_email=email,
    )


def get_retry_job_use_case() -> RetryJobUseCase:
    return RetryJobUseCase(
        job_repository=get_job_repository(),
        translate_job_use_case=get_translate_job_use_case(),
    )


def get_jobs_use_case() -> GetJobsUseCase:
    return GetJobsUseCase(
        job_repository=get_job_repository(),
    )


def get_clean_old_jobs_use_case() -> CleanOldJobsUseCase:
    return CleanOldJobsUseCase(
        job_repository=get_job_repository(),
    )
