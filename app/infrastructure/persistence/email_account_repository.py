"""
Infrastructure: Email Account Repository — CRUD cho bảng email_accounts.
"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.infrastructure.persistence.email_account_orm import EmailAccountORM


class EmailAccountRepository:

    def __init__(self, session_factory):
        self._session_factory = session_factory

    def get_active(self) -> Optional[EmailAccountORM]:
        """Lấy email account đang active (cái đầu tiên)."""
        with self._session_factory() as session:
            return (
                session.query(EmailAccountORM)
                .filter_by(is_active=True)
                .order_by(EmailAccountORM.updated_at.desc())
                .first()
            )

    def get_by_email(self, email_address: str) -> Optional[EmailAccountORM]:
        """Tìm account theo email address."""
        with self._session_factory() as session:
            return (
                session.query(EmailAccountORM)
                .filter_by(email_address=email_address.lower().strip())
                .first()
            )

    def save(
        self,
        email_address: str,
        app_password_encrypted: str,
        display_name: str = "",
        avatar_url: str = "",
        imap_host: str = "imap.gmail.com",
        imap_port: int = 993,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
    ) -> EmailAccountORM:
        """Tạo mới hoặc cập nhật email account."""
        email_lower = email_address.lower().strip()
        with self._session_factory() as session:
            existing = (
                session.query(EmailAccountORM)
                .filter_by(email_address=email_lower)
                .first()
            )
            if existing:
                existing.app_password_encrypted = app_password_encrypted
                existing.display_name = display_name or existing.display_name
                existing.avatar_url = avatar_url or existing.avatar_url
                existing.imap_host = imap_host
                existing.imap_port = imap_port
                existing.smtp_host = smtp_host
                existing.smtp_port = smtp_port
                existing.is_active = True
                session.commit()
                session.refresh(existing)
                return existing
            else:
                account = EmailAccountORM(
                    email_address=email_lower,
                    app_password_encrypted=app_password_encrypted,
                    display_name=display_name,
                    avatar_url=avatar_url,
                    imap_host=imap_host,
                    imap_port=imap_port,
                    smtp_host=smtp_host,
                    smtp_port=smtp_port,
                    is_active=True,
                )
                session.add(account)
                session.commit()
                session.refresh(account)
                return account

    def update_verified(self, email_address: str) -> None:
        """Cập nhật thời gian verify cuối cùng."""
        with self._session_factory() as session:
            account = (
                session.query(EmailAccountORM)
                .filter_by(email_address=email_address.lower().strip())
                .first()
            )
            if account:
                account.last_verified_at = datetime.now(timezone.utc)
                session.commit()

    def delete_by_email(self, email_address: str) -> bool:
        """Xóa account theo email. Trả về True nếu đã xóa."""
        with self._session_factory() as session:
            account = (
                session.query(EmailAccountORM)
                .filter_by(email_address=email_address.lower().strip())
                .first()
            )
            if account:
                session.delete(account)
                session.commit()
                return True
            return False

    def get_all(self) -> list[EmailAccountORM]:
        """Lấy tất cả email accounts."""
        with self._session_factory() as session:
            return session.query(EmailAccountORM).all()
