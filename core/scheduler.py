"""
Background Scheduler — APScheduler
Chạy job định kỳ: poll email + dịch file
"""
import logging
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")

# Lock để tránh chạy đồng thời (scheduler + manual trigger)
_running_lock = threading.Lock()


def _poll_and_process():
    """Job định kỳ: đọc email → tạo jobs → dịch ngay."""
    # Nếu đang có instance khác chạy thì bỏ qua
    if not _running_lock.acquire(blocking=False):
        logger.warning("⏩ Đang có lần quét khác chạy, bỏ qua lần này.")
        return

    try:
        from core.dependencies import get_process_email_use_case, get_translate_job_use_case
        logger.info("⏰ Scheduler: Bắt đầu kiểm tra email mới...")

        # Bước 1: Đọc email, tạo job mới
        process_uc = get_process_email_use_case()
        new_jobs = process_uc.execute()

        # Bước 2: Dịch tất cả job đang PENDING (bao gồm cả job mới và job cũ chưa xử lý)
        translate_uc = get_translate_job_use_case()
        processed = translate_uc.execute_pending()
        if processed > 0:
            logger.info(f"✅ Scheduler: Đã dịch xong {processed} bài.")
        elif not new_jobs:
            logger.info("💤 Scheduler: Không có email mới hoặc job pending.")

        # Bước 3: Tự động dọn dẹp các job và file dịch cũ hơn 1 tuần (7 ngày)
        try:
            from core.dependencies import get_clean_old_jobs_use_case
            clean_uc = get_clean_old_jobs_use_case()
            deleted = clean_uc.execute(days=7)
            if deleted > 0:
                logger.info(f"🧹 Scheduler: Đã dọn dẹp {deleted} bài dịch cũ quá 1 tuần.")
        except Exception as clean_err:
            logger.error(f"Lỗi dọn dẹp job cũ: {clean_err}")

    except Exception as e:
        logger.error(f"❌ Scheduler lỗi: {e}", exc_info=True)
    finally:
        _running_lock.release()


def start_scheduler(poll_interval_seconds: int = 300):
    """Khởi động scheduler với interval đã cấu hình."""
    _scheduler.add_job(
        _poll_and_process,
        trigger=IntervalTrigger(seconds=poll_interval_seconds),
        id="poll_and_process",
        name="Kiểm tra email và dịch file",
        replace_existing=True,
        max_instances=1,  # APScheduler cũng không chạy đồng thời
    )
    _scheduler.start()
    minutes = poll_interval_seconds / 60
    logger.info(f"🕐 Scheduler đã khởi động. Kiểm tra email mỗi {minutes:.0f} phút.")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("🛑 Scheduler đã dừng.")


def trigger_now():
    """Chạy thủ công ngay lập tức (dùng cho API endpoint).
    Chạy trong thread riêng để không block HTTP response.
    """
    t = threading.Thread(target=_poll_and_process, daemon=True)
    t.start()

