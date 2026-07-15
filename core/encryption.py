"""
Core: Fernet Encryption — mã hóa/giải mã App Password trước khi lưu DB.
Sử dụng SECRET_KEY từ .env làm encryption key.
"""
import base64
import hashlib
# pyrefly: ignore [missing-import]
from cryptography.fernet import Fernet


def _derive_key(secret: str) -> bytes:
    """Derive a 32-byte Fernet key from an arbitrary secret string."""
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_password(plain_password: str, secret_key: str) -> str:
    """Mã hóa password thành chuỗi encrypted (base64). Trả về string để lưu DB."""
    fernet = Fernet(_derive_key(secret_key))
    return fernet.encrypt(plain_password.encode("utf-8")).decode("utf-8")


def decrypt_password(encrypted_password: str, secret_key: str) -> str:
    """Giải mã password từ chuỗi encrypted. Trả về plain text."""
    fernet = Fernet(_derive_key(secret_key))
    return fernet.decrypt(encrypted_password.encode("utf-8")).decode("utf-8")
