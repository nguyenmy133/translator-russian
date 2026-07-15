"""
Presentation: Auth Middleware — bảo vệ API routes bằng JWT cookie.
Các route KHÔNG cần auth: /api/auth/*, /docs, /openapi.json
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request

from core.config import get_settings
from core.jwt_utils import verify_token

logger = logging.getLogger(__name__)

# Routes không cần authentication
PUBLIC_PATHS = {
    "/api/auth/google",
    "/api/auth/logout",
    "/api/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}

# Prefixes không cần auth (static assets, SPA)
PUBLIC_PREFIXES = (
    "/assets/",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware kiểm tra JWT cookie trên mọi /api/* request."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Bỏ qua các route public
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Bỏ qua static assets
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Chỉ protect /api/* routes
        if not path.startswith("/api/"):
            return await call_next(request)

        # Kiểm tra JWT cookie
        token = request.cookies.get("auth_token")
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Chưa đăng nhập"},
            )

        settings = get_settings()
        payload = verify_token(token, settings.secret_key)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Phiên đăng nhập đã hết hạn"},
            )

        # Gắn user info vào request state để các endpoint sử dụng
        request.state.user_email = payload.get("email", "")
        request.state.user_name = payload.get("name", "")
        request.state.user_picture = payload.get("picture", "")

        return await call_next(request)
