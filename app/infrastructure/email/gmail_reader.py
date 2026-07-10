"""
Infrastructure: Gmail IMAP Adapter — implements IEmailReader

Fix v2 — Giải quyết vấn đề với hòm thư có nhiều email unread:
  1. Dùng IMAP SEARCH UNSEEN với filter HAS_ATTACHMENT để giảm số email phải duyệt
  2. Dùng BODY.PEEK[HEADER] + BODY.PEEK[TEXT] thay vì RFC822 để tránh mark-as-read và timeout
  3. Xử lý từng email với reconnect nếu bị ngắt kết nối
  4. Giới hạn số email xử lý mỗi lần (MAX_EMAILS_PER_POLL)
  5. Thêm socket timeout để tránh treo vô hạn
"""
import imaplib
import email
import re
import socket
import logging
from email.header import decode_header
from email.message import Message
from typing import Optional

from app.application.ports.email_port import IEmailReader, IncomingEmail, EmailAttachment

logger = logging.getLogger(__name__)

# Tối đa số email kiểm tra mỗi lần quét (tránh timeout với hòm thư nhiều email)
MAX_EMAILS_PER_POLL = 50
# Timeout kết nối IMAP (giây)
IMAP_TIMEOUT_SECONDS = 30


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


def _connect_imap(host: str, port: int, email_address: str, password: str) -> imaplib.IMAP4_SSL:
    """Tạo kết nối IMAP mới với timeout."""
    # Set socket timeout toàn cục trước khi connect
    socket.setdefaulttimeout(IMAP_TIMEOUT_SECONDS)
    mail = imaplib.IMAP4_SSL(host, port)
    mail.login(email_address, password)
    mail.select("INBOX")
    return mail


class GmailIMAPReader(IEmailReader):
    """Kết nối Gmail qua IMAP SSL, tìm email chưa đọc có file Word tiếng Nga."""

    def __init__(self, host: str, port: int, email_address: str, app_password: str, allowed_senders: str = "*"):
        self._host = host
        self._port = port
        self._email = email_address
        self._password = app_password
        
        # Whitelist senders
        if not allowed_senders or allowed_senders.strip() == "*":
            self._allow_all_senders = True
            self._allowed_senders_set = set()
        else:
            self._allow_all_senders = False
            self._allowed_senders_set = {
                s.strip().lower() for s in allowed_senders.split(",") if s.strip()
            }

    def _sort_attachments_by_subject(self, attachments: list[EmailAttachment], subject: str) -> list[EmailAttachment]:
        if not attachments or len(attachments) <= 1 or not subject:
            return attachments

        # Chuẩn hóa tiêu đề: chỉ giữ lại chữ cái và chữ số viết thường
        clean_subj = re.sub(r'[^a-z0-9]', '', subject.lower())

        def get_sorting_index(att: EmailAttachment) -> int:
            filename = att.filename.lower()
            words = re.findall(r'[a-z]+', filename)
            
            best_index = len(clean_subj)
            for word in words:
                # Chỉ xét từ có độ dài từ 3 ký tự trở lên và không phải định dạng phần mở rộng
                if len(word) >= 3 and word not in ('doc', 'docx') and word in clean_subj:
                    idx = clean_subj.find(word)
                    if idx < best_index:
                        best_index = idx
            return best_index

        return sorted(attachments, key=get_sorting_index)

    def fetch_unread_with_docx(self) -> list[IncomingEmail]:
        results: list[IncomingEmail] = []
        mail = None

        try:
            mail = _connect_imap(self._host, self._port, self._email, self._password)

            # ── Bước 1: Search email UNSEEN ──────────────────────────────
            status, data = mail.uid("search", None, "UNSEEN")
            if status != "OK" or not data[0]:
                logger.info("📭 Không có email chưa đọc.")
                return []

            all_uids = data[0].split()
            total_unread = len(all_uids)
            logger.info(f"📬 {total_unread} email chưa đọc. Kiểm tra {min(total_unread, MAX_EMAILS_PER_POLL)} email mới nhất.")

            # ── Bước 2: Lấy các email MỚI NHẤT trước ─────────────────────
            uids_to_check = all_uids[-MAX_EMAILS_PER_POLL:]
            if not uids_to_check:
                return []

            # ── Bước 3: Bulk fetch HEADER cho các email này ──────────────
            uid_csv = ",".join([uid.decode() for uid in uids_to_check])
            logger.info(f"⚡ Đang tải tiêu đề hàng loạt cho {len(uids_to_check)} email...")
            status, fetch_data = mail.uid(
                "fetch", uid_csv, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT CONTENT-TYPE MESSAGE-ID)])"
            )
            if status != "OK" or not fetch_data:
                logger.warning("⚠️ Không thể tải tiêu đề email hàng loạt.")
                return []

            # Map UID -> Header data
            headers_map = {}
            for item in fetch_data:
                if not isinstance(item, tuple):
                    continue
                envelope = item[0].decode(errors="replace")
                raw_header = item[1]
                uid_match = re.search(r"UID\s+(\d+)", envelope)
                if uid_match:
                    headers_map[uid_match.group(1)] = raw_header

            # Duyệt qua các UID theo thứ tự thời gian (cũ nhất trước - FIFO)
            for uid in uids_to_check:
                uid_str = uid.decode()
                raw_header = headers_map.get(uid_str)
                if not raw_header:
                    continue

                try:
                    header_msg = email.message_from_bytes(raw_header)

                    # Lọc người gửi qua whitelist động
                    from_header = _decode_str(header_msg.get("From", ""))
                    _, sender_email = _parse_sender(from_header)
                    sender_email = sender_email.lower().strip()

                    if not self._allow_all_senders and sender_email not in self._allowed_senders_set:
                        # Bỏ qua hoàn toàn và GIỮ NGUYÊN trạng thái chưa đọc (UNREAD)
                        continue

                    # Kiểm tra Content-Type header để đoán có attachment
                    content_type = header_msg.get("Content-Type", "")
                    if "multipart" not in content_type.lower():
                        continue

                    # ── Bước 4: Fetch full message CHỈ KHI có multipart ──
                    status, msg_data = mail.uid("fetch", uid, "(BODY.PEEK[])")
                    if status != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_bytes = msg_data[0][1] if isinstance(msg_data[0], tuple) else None
                    if not raw_bytes:
                        continue

                    msg: Message = email.message_from_bytes(raw_bytes)
                    attachments = self._extract_ru_docx(msg)

                    if not attachments:
                        continue

                    # Sắp xếp các file đính kèm theo thứ tự tiêu đề
                    subject_str = _decode_str(msg.get("Subject", ""))
                    attachments = self._sort_attachments_by_subject(attachments, subject_str)

                    # ── Bước 5: Có file hợp lệ → lưu kết quả và đánh dấu ĐÃ ĐỌC (Seen) ──
                    sender_name, _ = _parse_sender(from_header)

                    # Lấy Message-ID
                    message_id = header_msg.get("Message-ID", "").strip()

                    # Đánh dấu đã đọc trong Gmail
                    mail.uid("store", uid, "+FLAGS", "\\Seen")

                    results.append(IncomingEmail(
                        uid=uid_str,
                        sender_email=sender_email,
                        sender_name=sender_name,
                        subject=subject_str,
                        attachments=attachments,
                        message_id=message_id,
                    ))
                    logger.info(f"📎 Tìm thấy file Nga từ {sender_email}: {[a.filename for a in attachments]} (UID: {uid_str})")

                except imaplib.IMAP4.error as uid_err:
                    logger.warning(f"⚠️ Lỗi xử lý UID {uid_str}: {uid_err}. Thử reconnect...")
                    try:
                        mail.logout()
                    except Exception:
                        pass
                    try:
                        mail = _connect_imap(self._host, self._port, self._email, self._password)
                    except Exception as reconnect_err:
                        logger.error(f"❌ Không thể reconnect IMAP: {reconnect_err}")
                        break
                    continue

        except imaplib.IMAP4.error as e:
            logger.error(f"❌ IMAP error: {e}")
        except Exception as e:
            logger.error(f"❌ Lỗi đọc email: {e}", exc_info=True)
        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass
            socket.setdefaulttimeout(None)

        return results

    @staticmethod
    def _extract_ru_docx(msg: Message) -> list[EmailAttachment]:
        found = []
        for part in msg.walk():
            content_disposition = part.get("Content-Disposition", "")
            if "attachment" not in content_disposition:
                continue
            raw_name = part.get_filename()
            if not raw_name:
                continue
            filename = _decode_str(raw_name)
            if _is_russian_docx(filename):
                content = part.get_payload(decode=True)
                if content:
                    found.append(EmailAttachment(filename=filename, content=content))
        return found
