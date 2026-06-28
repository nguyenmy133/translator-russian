"""
Application Ports — Email
Giao diện thuần túy cho infrastructure adapter triển khai.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmailAttachment:
    """Value object đại diện cho một file đính kèm email."""
    filename: str
    content: bytes


@dataclass
class IncomingEmail:
    """Value object đại diện cho một email nhận vào."""
    uid: str
    sender_email: str
    sender_name: str
    subject: str
    attachments: list[EmailAttachment]
    message_id: Optional[str] = None


class IEmailReader(ABC):
    """Port: Đọc email mới từ hộp thư."""

    @abstractmethod
    def fetch_unread_with_docx(self) -> list[IncomingEmail]:
        """
        Trả về danh sách email chưa đọc có đính kèm .docx chứa '(ru)'.
        """
        ...


class IEmailSender(ABC):
    """Port: Gửi email với kết quả dịch."""

    @abstractmethod
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
        ...

    @abstractmethod
    def send_failure(
        self,
        to_email: str,
        original_filename: str,
        error: str,
        original_message_id: Optional[str] = None,
    ) -> None:
        ...
