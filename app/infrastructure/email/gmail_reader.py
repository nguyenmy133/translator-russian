"""
Infrastructure: Gmail IMAP Adapter — implements IEmailReader
"""
import imaplib
import email
import re
import logging
from email.header import decode_header
from email.message import Message
from typing import Optional

from app.application.ports.email_port import IEmailReader, IncomingEmail, EmailAttachment

logger = logging.getLogger(__name__)


def _decode_str(s) -> str:
    if s is None:
        return ""
    parts = decode_header(s)
    result = ""
    for part, charset in parts:
        if isinstance(part, bytes):
            result += part.decode(charset or "utf-8", errors="replace")
        else:
            result += str(part)
    return result


def _is_russian_docx(filename: str) -> bool:
    """
    Nhận diện file Word tiếng Nga. Hỗ trợ các format thực tế:
      - "23.06 GBPUSD ru.docx"   ← format thực tế (space + ru, KHÔNG ngoặc)
      - "abc (ru).docx"          ← format có ngoặc tròn
      - "abc(ru).docx"           ← format có ngoặc không space

    Và bỏ qua các bài có chứa từ "audio" trong tên file.
    """
    if not filename:
        return False
    name = filename.lower().strip()

    # Bỏ qua các file audio (chứa từ "audio")
    if "audio" in name:
        return False

    if not name.endswith(".docx"):
        return False
    # Pattern 1: kết thúc bằng " ru.docx" (space trước ru, không ngoặc) — format thực tế
    if re.search(r'\sru\.docx$', name):
        return True
    # Pattern 2: chứa "(ru)" ở bất kỳ đâu trong tên — format có ngoặc
    if re.search(r'\(ru\)', name):
        return True
    return False


def _parse_sender(from_header: str) -> tuple[str, str]:
    match = re.match(r"^(.*?)\s*<([^>]+)>$", from_header.strip())
    if match:
        return match.group(1).strip().strip('"'), match.group(2).strip()
    return "", from_header.strip()


class GmailIMAPReader(IEmailReader):
    """Kết nối Gmail qua IMAP SSL, tìm email chưa đọc có file Word tiếng Nga."""

    def __init__(self, host: str, port: int, email_address: str, app_password: str):
        self._host = host
        self._port = port
        self._email = email_address
        self._password = app_password

    def fetch_unread_with_docx(self) -> list[IncomingEmail]:
        results: list[IncomingEmail] = []

        try:
            mail = imaplib.IMAP4_SSL(self._host, self._port)
            mail.login(self._email, self._password)
            mail.select("INBOX")

            status, data = mail.uid("search", None, "UNSEEN")
            if status != "OK" or not data[0]:
                logger.info("📭 Không có email chưa đọc.")
                mail.logout()
                return []

            uids = data[0].split()
            logger.info(f"📬 {len(uids)} email chưa đọc.")

            for uid in uids:
                uid_str = uid.decode()
                status, msg_data = mail.uid("fetch", uid, "(RFC822)")
                if status != "OK":
                    continue

                msg: Message = email.message_from_bytes(msg_data[0][1])
                attachments = self._extract_ru_docx(msg)

                if not attachments:
                    # Email không có file Word tiếng Nga → bỏ đánh dấu đã đọc
                    mail.uid("store", uid, "-FLAGS", "\\Seen")
                    continue

                from_header = _decode_str(msg.get("From", ""))
                sender_name, sender_email = _parse_sender(from_header)

                results.append(IncomingEmail(
                    uid=uid_str,
                    sender_email=sender_email,
                    sender_name=sender_name,
                    subject=_decode_str(msg.get("Subject", "")),
                    attachments=attachments,
                ))

            mail.logout()

        except imaplib.IMAP4.error as e:
            logger.error(f"❌ IMAP error: {e}")
        except Exception as e:
            logger.error(f"❌ Lỗi đọc email: {e}")

        return results

    @staticmethod
    def _extract_ru_docx(msg: Message) -> list[EmailAttachment]:
        found = []
        for part in msg.walk():
            if "attachment" not in part.get("Content-Disposition", ""):
                continue
            raw_name = part.get_filename()
            if not raw_name:
                continue
            filename = _decode_str(raw_name)
            if _is_russian_docx(filename):
                content = part.get_payload(decode=True)
                found.append(EmailAttachment(filename=filename, content=content))
        return found
