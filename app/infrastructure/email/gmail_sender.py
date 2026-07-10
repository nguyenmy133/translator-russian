"""
Infrastructure: Gmail SMTP Adapter — implements IEmailSender
"""
import smtplib
import logging
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from app.application.ports.email_port import IEmailSender

logger = logging.getLogger(__name__)


class GmailSMTPSender(IEmailSender):

    def __init__(self, host: str, port: int, email_address: str, app_password: str):
        self._host = host
        self._port = port
        self._email = email_address
        self._password = app_password

    def send_success(
        self,
        to_email: str,
        to_name: str,
        original_filename: str,
        translated_file_path: str,
        translated_filename: str,
        paragraph_count: int,
        char_count: int,
        file_only: bool = False,
        original_message_id: Optional[str] = None,
        original_subject: Optional[str] = None,
    ) -> None:
        msg = MIMEMultipart()
        msg["From"] = self._email
        msg["To"] = to_email

        if original_message_id:
            msg["In-Reply-To"] = original_message_id
            msg["References"] = original_message_id

        if file_only:
            # Thiết lập tiêu đề để gộp luồng email của khách hàng
            if original_subject:
                subj = original_subject.strip()
                if not subj.lower().startswith("re:"):
                    subj = f"Re: {subj}"
                msg["Subject"] = subj
            # Tránh gửi email có thân thư hoàn toàn trống để tránh bị đánh dấu Spam
            body_text = (
                f"Chào bạn {to_name or ''},\n\n"
                f"Hệ thống dịch thuật tự động gửi bạn bản dịch tiếng Việt của tài liệu \"{original_filename}\" đính kèm bên dưới.\n\n"
                f"Trân trọng,\nEmail Translator System"
            )
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
        else:
            # Thư báo dịch thành công cho chủ hệ thống
            msg["Subject"] = f"Dịch thành công file {original_filename}"
            body = self._success_html(
                to_name, original_filename, translated_filename,
                paragraph_count, char_count
            )
            msg.attach(MIMEText(body, "html", "utf-8"))

        # Chỉ đính kèm file khi gửi cho khách hàng (file_only=True)
        if file_only:
            with open(translated_file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{translated_filename}"')
            msg.attach(part)

        self._send(to_email, msg)
        logger.info(f"📤 Gửi thành công ({'chỉ file' if file_only else 'thông báo'}) → {to_email}: {translated_filename}")

    def send_failure(
        self,
        to_email: str,
        original_filename: str,
        error: str,
        original_message_id: Optional[str] = None,
    ) -> None:
        msg = MIMEMultipart()
        msg["From"] = self._email
        msg["To"] = to_email
        msg["Subject"] = f"❌ [Lỗi dịch] {original_filename}"

        if original_message_id:
            msg["In-Reply-To"] = original_message_id
            msg["References"] = original_message_id

        body = f"""
        <html><body style="font-family:Arial,sans-serif;padding:20px;">
            <h2 style="color:#e74c3c;">⚠️ Không thể dịch file</h2>
            <p>File <strong>{original_filename}</strong> gặp lỗi khi dịch.</p>
            <p><strong>Chi tiết:</strong> {error}</p>
            <p>Vui lòng thử lại hoặc liên hệ quản trị viên.</p>
        </body></html>
        """
        msg.attach(MIMEText(body, "html", "utf-8"))
        self._send(to_email, msg)

    def _send(self, to_email: str, msg: MIMEMultipart) -> None:
        with smtplib.SMTP(self._host, self._port) as server:
            server.ehlo()
            server.starttls()
            server.login(self._email, self._password)
            server.sendmail(self._email, to_email, msg.as_string())

    @staticmethod
    def _success_html(
        to_name: str, original: str, translated: str,
        paragraphs: int, chars: int
    ) -> str:
        name = to_name or "bạn"
        return f"""
        <html>
        <body style="font-family:'Segoe UI',Arial,sans-serif;background:#f4f7f9;margin:0;padding:20px;">
          <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:30px;text-align:center;">
              <h1 style="color:#fff;margin:0;font-size:22px;">🌐 Dịch Thuật Hoàn Thành</h1>
              <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;">Tiếng Nga → Tiếng Việt</p>
            </div>
            <div style="padding:28px;">
              <p>Xin chào <strong>{name}</strong>,</p>
              <p>File của bạn đã được dịch thành công! 🎉</p>
              <div style="background:#f8f9ff;border-left:4px solid #667eea;border-radius:8px;padding:16px;margin:20px 0;">
                <p style="margin:0 0 8px;"><strong>📄 File gốc:</strong> {original}</p>
                <p style="margin:0 0 8px;"><strong>✅ File đã dịch:</strong> {translated}</p>
                <p style="margin:0 0 8px;"><strong>📊 Số đoạn văn:</strong> {paragraphs}</p>
                <p style="margin:0;"><strong>🔤 Ký tự đã dịch:</strong> {chars:,}</p>
              </div>
              <p>File đã được đính kèm. Vui lòng kiểm tra chất lượng dịch.</p>
              <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
              <p style="color:#999;font-size:11px;text-align:center;">Hệ thống dịch tự động | Powered by Google Translate (Free)</p>
            </div>
          </div>
        </body>
        </html>
        """
