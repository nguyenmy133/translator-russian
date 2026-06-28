"""
Infrastructure: SQLAlchemy implementation of IJobRepository.
Mapper pattern: ORM model ↔ Domain entity.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.domain.entities.translation_job import TranslationJob
from app.domain.repositories.job_repository import IJobRepository
from app.domain.value_objects.job_status import JobStatus
from app.infrastructure.persistence.orm_models import TranslationJobORM


class SQLiteJobRepository(IJobRepository):

    def __init__(self, session_factory):
        self._session_factory = session_factory

    # ──────────────────────────────────────────────────────────
    # IJobRepository implementation
    # ──────────────────────────────────────────────────────────

    def save(self, job: TranslationJob) -> TranslationJob:
        with self._session_factory() as session:
            if job.id is None:
                orm = self._to_orm(job)
                session.add(orm)
                session.commit()
                session.refresh(orm)
                job.id = orm.id
            else:
                orm = session.query(TranslationJobORM).filter_by(id=job.id).first()
                if orm is None:
                    raise ValueError(f"Job #{job.id} không tồn tại trong DB")
                self._update_orm(orm, job)
                session.commit()
                session.refresh(orm)
            return self._to_entity(orm)

    def find_by_id(self, job_id: int) -> Optional[TranslationJob]:
        with self._session_factory() as session:
            orm = session.query(TranslationJobORM).filter_by(id=job_id).first()
            return self._to_entity(orm) if orm else None

    def find_by_email_uid(self, email_uid: str) -> Optional[TranslationJob]:
        with self._session_factory() as session:
            orm = session.query(TranslationJobORM).filter_by(email_uid=email_uid).first()
            return self._to_entity(orm) if orm else None

    def find_by_status(self, status: JobStatus) -> list[TranslationJob]:
        with self._session_factory() as session:
            orms = (
                session.query(TranslationJobORM)
                .filter_by(status=status.value)
                .order_by(TranslationJobORM.created_at.asc())
                .all()
            )
            return [self._to_entity(o) for o in orms]

    def find_all(self, limit: int = 100, offset: int = 0) -> list[TranslationJob]:
        with self._session_factory() as session:
            orms = (
                session.query(TranslationJobORM)
                .order_by(TranslationJobORM.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            return [self._to_entity(o) for o in orms]

    def count_by_status(self, status: JobStatus) -> int:
        with self._session_factory() as session:
            return session.query(TranslationJobORM).filter_by(status=status.value).count()

    def find_older_than_days(self, days: int) -> list[TranslationJob]:
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        with self._session_factory() as session:
            orms = (
                session.query(TranslationJobORM)
                .filter(TranslationJobORM.created_at < cutoff)
                .all()
            )
            return [self._to_entity(o) for o in orms]

    def delete(self, job_id: int) -> None:
        with self._session_factory() as session:
            orm = session.query(TranslationJobORM).filter_by(id=job_id).first()
            if orm:
                session.delete(orm)
                session.commit()

    # ──────────────────────────────────────────────────────────
    # Mapper methods (ORM ↔ Domain Entity)
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(orm: TranslationJobORM) -> TranslationJob:
        return TranslationJob(
            id=orm.id,
            original_filename=orm.original_filename,
            translated_filename=orm.translated_filename,
            original_path=orm.original_path,
            translated_path=orm.translated_path,
            sender_email=orm.sender_email,
            sender_name=orm.sender_name or "",
            subject=orm.subject or "",
            email_uid=orm.email_uid or "",
            message_id=orm.message_id,
            status=JobStatus(orm.status),
            error_message=orm.error_message,
            char_count=orm.char_count or 0,
            paragraph_count=orm.paragraph_count or 0,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            completed_at=orm.completed_at,
        )

    @staticmethod
    def _to_orm(job: TranslationJob) -> TranslationJobORM:
        return TranslationJobORM(
            original_filename=job.original_filename,
            translated_filename=job.translated_filename,
            original_path=job.original_path,
            translated_path=job.translated_path,
            sender_email=job.sender_email,
            sender_name=job.sender_name,
            subject=job.subject,
            email_uid=job.email_uid,
            message_id=job.message_id,
            status=job.status.value,
            error_message=job.error_message,
            char_count=job.char_count,
            paragraph_count=job.paragraph_count,
        )

    @staticmethod
    def _update_orm(orm: TranslationJobORM, job: TranslationJob) -> None:
        orm.translated_filename = job.translated_filename
        orm.translated_path = job.translated_path
        orm.status = job.status.value
        orm.error_message = job.error_message
        orm.char_count = job.char_count
        orm.paragraph_count = job.paragraph_count
        orm.completed_at = job.completed_at
        orm.updated_at = job.updated_at
