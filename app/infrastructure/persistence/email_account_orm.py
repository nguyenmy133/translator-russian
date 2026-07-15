"""
Infrastructure: SQLAlchemy ORM Model — bảng email_accounts
Lưu trữ cấu hình email account (encrypted app password).
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.infrastructure.persistence.database import Base


class EmailAccountORM(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email_address = Column(String(255), unique=True, nullable=False, index=True)
    app_password_encrypted = Column(Text, nullable=True)

    # IMAP/SMTP settings
    imap_host = Column(String(255), default="imap.gmail.com")
    imap_port = Column(Integer, default=993)
    smtp_host = Column(String(255), default="smtp.gmail.com")
    smtp_port = Column(Integer, default=587)

    # Google profile info
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
