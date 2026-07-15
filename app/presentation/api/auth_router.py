"""
Presentation: Auth Router — Google OAuth2 login/logout.
Verify Google ID token → tạo JWT → set HttpOnly cookie.
"""
import logging
from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from core.config import get_settings
from core.jwt_utils import create_token, verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth")

_settings = get_settings()
COOKIE_NAME = "auth_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days


class GoogleLoginRequest(BaseModel):
    id_token: str


@router.post("/google")
async def google_login(body: GoogleLoginRequest, response: Response):
    """Verify Google ID token và tạo session JWT."""
    try:
        # Verify token với Google
        idinfo = id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            _settings.google_client_id,
        )

        # Lấy thông tin user
        email = idinfo.get("email", "")
        name = idinfo.get("name", "")
        picture = idinfo.get("picture", "")

        if not email:
            raise HTTPException(status_code=400, detail="Không lấy được email từ Google")

        # Tạo JWT
        jwt_token = create_token(
            payload={
                "email": email,
                "name": name,
                "picture": picture,
            },
            secret_key=_settings.secret_key,
        )

        # Set HttpOnly cookie
        response.set_cookie(
            key=COOKIE_NAME,
            value=jwt_token,
            httponly=True,
            secure=False,  # Set True cho production HTTPS
            samesite="lax",
            max_age=COOKIE_MAX_AGE,
            path="/",
        )

        logger.info(f"✅ Google login thành công: {email}")
        return {
            "message": "Đăng nhập thành công",
            "user": {
                "email": email,
                "name": name,
                "picture": picture,
            },
        }

    except ValueError as e:
        logger.warning(f"⚠️ Google token không hợp lệ: {e}")
        raise HTTPException(status_code=401, detail="Token Google không hợp lệ")
    except Exception as e:
        logger.error(f"❌ Lỗi Google login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Lỗi xác thực Google")


@router.get("/me")
async def get_current_user(request: Request):
    """Trả về thông tin user hiện tại từ JWT cookie."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")

    payload = verify_token(token, _settings.secret_key)
    if not payload:
        raise HTTPException(status_code=401, detail="Token hết hạn")

    return {
        "email": payload.get("email", ""),
        "name": payload.get("name", ""),
        "picture": payload.get("picture", ""),
    }


@router.post("/logout")
async def logout(response: Response):
    """Xóa cookie authentication."""
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Đã đăng xuất"}
