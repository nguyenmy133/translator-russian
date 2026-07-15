"""
Core: JWT Utilities — tạo và verify JWT token cho authentication.
"""
# pyrefly: ignore [missing-import]
import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Token hết hạn sau 7 ngày
TOKEN_EXPIRY_DAYS = 7


def create_token(payload: dict, secret_key: str) -> str:
    """Tạo JWT token với payload cho trước. Tự thêm exp claim."""
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
    data["iat"] = datetime.now(timezone.utc)
    return jwt.encode(data, secret_key, algorithm="HS256")


def verify_token(token: str, secret_key: str) -> Optional[dict]:
    """Verify và decode JWT token. Trả về payload hoặc None nếu không hợp lệ."""
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.warning("⚠️ JWT token đã hết hạn")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"⚠️ JWT token không hợp lệ: {e}")
        return None
