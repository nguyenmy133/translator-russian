"""
Infrastructure: SQLAlchemy ORM Models (tách biệt khỏi Domain Entities)
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.infrastructure.persistence.database import Base


class TranslationJobORM(Base):
    __tablename__ = "translation_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    original_filename = Column(String(500), nullable=False)
    translated_filename = Column(String(500), nullable=True)
    original_path = Column(String(1000), nullable=True)
    translated_path = Column(String(1000), nullable=True)

    sender_email = Column(String(255), nullable=False, index=True)
    sender_name = Column(String(255), nullable=True, default="")
    subject = Column(String(500), nullable=True, default="")
    email_uid = Column(String(255), nullable=True, unique=True, index=True)
    message_id = Column(String(500), nullable=True)

    status = Column(String(50), default="PENDING", nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    char_count = Column(Integer, default=0)
    paragraph_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
