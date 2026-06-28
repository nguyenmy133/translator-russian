"""
Dependency Injection Container
Wires all layers together — đây là nơi duy nhất biết về tất cả các class cụ thể.
"""
from functools import lru_cache
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from app.infrastructure.persistence.database import create_db_engine, create_session_factory, Base
from app.infrastructure.persistence.orm_models import TranslationJobORM  # noqa: trigger metadata
from app.infrastructure.persistence.job_repository_impl import SQLiteJobRepository
from app.infrastructure.email.gmail_reader import GmailIMAPReader
from app.infrastructure.email.gmail_sender import GmailSMTPSender
from app.infrastructure.translation.google_translator import GoogleTranslatorAdapter
from app.infrastructure.document.docx_parser import DocxParser

from app.application.use_cases.process_email_use_case import ProcessEmailUseCase
from app.application.use_cases.translate_job_use_case import TranslateJobUseCase
from app.application.use_cases.retry_job_use_case import RetryJobUseCase
from app.application.use_cases.get_jobs_use_case import GetJobsUseCase
from app.application.use_cases.clean_old_jobs_use_case import CleanOldJobsUseCase


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


def get_email_reader() -> GmailIMAPReader:
    return GmailIMAPReader(
        host=_settings.imap_host,
        port=_settings.imap_port,
        email_address=_settings.gmail_address,
        app_password=_settings.gmail_app_password,
    )


def get_email_sender() -> GmailSMTPSender:
    return GmailSMTPSender(
        host=_settings.smtp_host,
        port=_settings.smtp_port,
        email_address=_settings.gmail_address,
        app_password=_settings.gmail_app_password,
    )


def get_translator() -> GoogleTranslatorAdapter:
    return GoogleTranslatorAdapter(source="ru", target="vi")


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
    return TranslateJobUseCase(
        job_repository=get_job_repository(),
        translator=get_translator(),
        document_parser=get_document_parser(),
        email_sender=get_email_sender(),
        output_dir=_settings.output_dir,
        translator_email=_settings.gmail_address,
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
