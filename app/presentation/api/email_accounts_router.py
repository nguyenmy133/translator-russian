"""
Presentation: Email Accounts Router — cấu hình email trên UI.
Lưu/cập nhật App Password (mã hóa), test connection IMAP+SMTP.
"""
import imaplib
import smtplib
import socket
import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.config import get_settings
from core.encryption import encrypt_password, decrypt_password
from app.infrastructure.persistence.email_account_repository import EmailAccountRepository
from core.dependencies import get_email_account_repository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/email-accounts")

_settings = get_settings()
TEST_TIMEOUT = 10  # seconds


class SaveAccountRequest(BaseModel):
    app_password: str
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587


class TestConnectionRequest(BaseModel):
    email_address: str
    app_password: str
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587


@router.get("/status")
async def get_account_status(request: Request):
    """Trả về trạng thái cấu hình email (KHÔNG trả password)."""
    user_email = request.state.user_email
    repo = get_email_account_repository()
    account = repo.get_by_email(user_email)

    if not account or not account.app_password_encrypted:
        return {
            "configured": False,
            "email": user_email,
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "last_verified_at": None,
        }

    return {
        "configured": True,
        "email": account.email_address,
        "imap_host": account.imap_host,
        "imap_port": account.imap_port,
        "smtp_host": account.smtp_host,
        "smtp_port": account.smtp_port,
        "last_verified_at": account.last_verified_at.isoformat() if account.last_verified_at else None,
    }


@router.post("")
async def save_account(body: SaveAccountRequest, request: Request):
    """Lưu/cập nhật App Password (mã hóa) cho user đang login."""
    user_email = request.state.user_email
    user_name = request.state.user_name
    user_picture = request.state.user_picture

    # Mã hóa password
    encrypted = encrypt_password(body.app_password, _settings.secret_key)

    repo = get_email_account_repository()
    repo.save(
        email_address=user_email,
        app_password_encrypted=encrypted,
        display_name=user_name,
        avatar_url=user_picture,
        imap_host=body.imap_host,
        imap_port=body.imap_port,
        smtp_host=body.smtp_host,
        smtp_port=body.smtp_port,
    )

    logger.info(f"✅ Đã lưu cấu hình email: {user_email}")
    return {"message": "Đã lưu cấu hình email thành công"}


@router.post("/test")
async def test_connection(body: TestConnectionRequest):
    """Test kết nối IMAP + SMTP với credentials cho trước."""
    results = {"imap": {"success": False, "message": ""}, "smtp": {"success": False, "message": ""}}

    # Test IMAP
    try:
        socket.setdefaulttimeout(TEST_TIMEOUT)
        mail = imaplib.IMAP4_SSL(body.imap_host, body.imap_port)
        mail.login(body.email_address, body.app_password)
        mail.select("INBOX")
        results["imap"] = {"success": True, "message": "Kết nối IMAP thành công ✅"}
        mail.logout()
    except imaplib.IMAP4.error as e:
        results["imap"] = {"success": False, "message": f"Lỗi IMAP: {str(e)}"}
    except socket.timeout:
        results["imap"] = {"success": False, "message": "IMAP timeout — kiểm tra host/port"}
    except Exception as e:
        results["imap"] = {"success": False, "message": f"Lỗi: {str(e)}"}
    finally:
        socket.setdefaulttimeout(None)

    # Test SMTP
    try:
        server = smtplib.SMTP(body.smtp_host, body.smtp_port, timeout=TEST_TIMEOUT)
        server.ehlo()
        server.starttls()
        server.login(body.email_address, body.app_password)
        results["smtp"] = {"success": True, "message": "Kết nối SMTP thành công ✅"}
        server.quit()
    except smtplib.SMTPAuthenticationError:
        results["smtp"] = {"success": False, "message": "Sai email hoặc App Password"}
    except socket.timeout:
        results["smtp"] = {"success": False, "message": "SMTP timeout — kiểm tra host/port"}
    except Exception as e:
        results["smtp"] = {"success": False, "message": f"Lỗi: {str(e)}"}

    # Nếu cả 2 thành công, cập nhật verified time
    if results["imap"]["success"] and results["smtp"]["success"]:
        try:
            repo = get_email_account_repository()
            repo.update_verified(body.email_address)
        except Exception:
            pass

    overall_success = results["imap"]["success"] and results["smtp"]["success"]
    return {
        "success": overall_success,
        "results": results,
    }


@router.delete("")
async def delete_account(request: Request):
    """Xóa cấu hình email của user hiện tại."""
    user_email = request.state.user_email
    repo = get_email_account_repository()
    deleted = repo.delete_by_email(user_email)

    if deleted:
        logger.info(f"🗑️ Đã xóa cấu hình email: {user_email}")
        return {"message": "Đã xóa cấu hình email"}
    raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình email")
