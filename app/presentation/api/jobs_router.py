"""
Presentation: FastAPI JSON API Router (pure REST, no HTML templates)
"""
import threading
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from core.dependencies import get_jobs_use_case, get_retry_job_use_case
from core.scheduler import trigger_now

router = APIRouter(prefix="/api")


# ── Response Schemas ────────────────────────────────────────────────

class JobResponse(BaseModel):
    id: int
    original_filename: str
    translated_filename: str | None
    sender_email: str
    sender_name: str
    subject: str
    status: str
    error_message: str | None
    char_count: int
    paragraph_count: int
    created_at: str | None
    completed_at: str | None
    has_file: bool

    class Config:
        from_attributes = True


def _job_to_dict(job) -> dict:
    return {
        "id": job.id,
        "original_filename": job.original_filename,
        "translated_filename": job.translated_filename,
        "sender_email": job.sender_email,
        "sender_name": job.sender_name or "",
        "subject": job.subject or "",
        "status": job.status.value,
        "status_label": job.status.label_vi,
        "error_message": job.error_message,
        "char_count": job.char_count,
        "paragraph_count": job.paragraph_count,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "has_file": bool(
            job.translated_path and os.path.exists(job.translated_path)
        ),
        "is_retryable": job.is_retryable,
    }


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/jobs")
async def list_jobs(limit: int = 100, offset: int = 0):
    """Danh sách tất cả jobs."""
    uc = get_jobs_use_case()
    jobs = uc.get_all(limit=limit, offset=offset)
    return {"jobs": [_job_to_dict(j) for j in jobs]}


@router.get("/jobs/{job_id}")
async def get_job(job_id: int):
    """Chi tiết một job."""
    uc = get_jobs_use_case()
    job = uc.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job không tồn tại")
    return _job_to_dict(job)


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: int):
    """Retry job FAILED — chạy async trong background thread."""
    try:
        uc = get_retry_job_use_case()
        thread = threading.Thread(target=uc.execute, args=(job_id,), daemon=True)
        thread.start()
        return {"message": f"Job #{job_id} đang được retry."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs/{job_id}/download")
async def download_file(job_id: int):
    """Download file Word đã dịch."""
    uc = get_jobs_use_case()
    job = uc.get_by_id(job_id)
    if not job or not job.translated_path:
        raise HTTPException(status_code=404, detail="File không tồn tại")
    if not os.path.exists(job.translated_path):
        raise HTTPException(status_code=404, detail="File đã bị xóa")
    return FileResponse(
        path=job.translated_path,
        filename=job.translated_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/stats")
async def get_stats():
    """Thống kê tổng quan."""
    uc = get_jobs_use_case()
    stats = uc.get_stats()
    return {
        "total": stats.total,
        "pending": stats.pending,
        "processing": stats.processing,
        "done": stats.done,
        "failed": stats.failed,
    }


@router.post("/trigger")
async def trigger_poll():
    """Trigger quét email thủ công."""
    thread = threading.Thread(target=trigger_now, daemon=True)
    thread.start()
    return {"message": "Đang quét email... Refresh dashboard sau vài giây."}
