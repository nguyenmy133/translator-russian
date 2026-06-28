"""
FastAPI Application Entry Point
- Pure API backend (React frontend served separately or as build)
- CORS enabled for React dev server
- Scheduler chạy nền poll email mỗi 5 phút
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.config import get_settings
from core.dependencies import init_database
from core.scheduler import start_scheduler, stop_scheduler
from app.presentation.api.jobs_router import router as jobs_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & Shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────────────
    logger.info("🚀 Khởi động Email Translator...")
    
    # Đảm bảo thư mục chứa database tồn tại (nếu dùng sqlite)
    if settings.database_url.startswith("sqlite:///"):
        db_file = settings.database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_file)
        if db_dir and db_dir not in (".", "./", ""):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"📁 Đã tạo thư mục database: {db_dir}")

    init_database()
    logger.info("✅ Database đã sẵn sàng.")

    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)

    start_scheduler(poll_interval_seconds=settings.poll_interval_seconds)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    stop_scheduler()
    logger.info("🛑 Email Translator đã dừng.")


app = FastAPI(
    title="Email Translator API",
    description="Tự động dịch file Word từ tiếng Nga sang tiếng Việt qua email",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (cho React dev server chạy ở port 5173) ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev
        "http://localhost:3000",   # CRA dev
        "http://127.0.0.1:5173",
        os.getenv("FRONTEND_URL", ""),  # Production URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ────────────────────────────────────────────────────────
app.include_router(jobs_router)


# ── Serve React Build (production) ───────────────────────────────────
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(FRONTEND_BUILD):
    # Mount assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """SPA fallback — mọi route không phải /api đều trả về index.html."""
        index = os.path.join(FRONTEND_BUILD, "index.html")
        return FileResponse(index)
else:
    @app.get("/", include_in_schema=False)
    async def dev_root():
        return {
            "message": "Email Translator API đang chạy",
            "docs": "/docs",
            "frontend": "Chạy: cd frontend && npm run dev",
        }
