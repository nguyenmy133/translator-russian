"""
Background Scheduler — APScheduler
Chạy 2 job định kỳ:
  1. poll_and_process: quét email mới + dịch ngay
  2. Có thể mở rộng: cleanup file cũ
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")


def _poll_and_process():
    """Job định kỳ: đọc email → tạo jobs → dịch ngay."""
    try:
        from core.dependencies import get_process_email_use_case, get_translate_job_use_case
        logger.info("⏰ Scheduler: Bắt đầu kiểm tra email mới...")

        # Bước 1: Đọc email, tạo job mới
        process_uc = get_process_email_use_case()
        new_jobs = process_uc.execute()

        # Bước 2: Dịch tất cả job đang PENDING (bao gồm cả job mới)
        if new_jobs or True:  # Luôn xử lý để catch job PENDING cũ
            translate_uc = get_translate_job_use_case()
            processed = translate_uc.execute_pending()
            if processed > 0:
                logger.info(f"✅ Scheduler: Đã dịch xong {processed} bài.")
        else:
            logger.info("💤 Scheduler: Không có job mới.")

    except Exception as e:
        logger.error(f"❌ Scheduler lỗi: {e}", exc_info=True)


def start_scheduler(poll_interval_seconds: int = 300):
    """Khởi động scheduler với interval đã cấu hình."""
    _scheduler.add_job(
        _poll_and_process,
        trigger=IntervalTrigger(seconds=poll_interval_seconds),
        id="poll_and_process",
        name="Kiểm tra email và dịch file",
        replace_existing=True,
        max_instances=1,  # Không chạy đồng thời 2 lần
    )
    _scheduler.start()
    logger.info(
        f"🕐 Scheduler đã khởi động. "
        f"Kiểm tra email mỗi {poll_interval_seconds // 60} phút."
    )


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("🛑 Scheduler đã dừng.")


def trigger_now():
    """Chạy thủ công ngay lập tức (dùng cho API endpoint)."""
    _poll_and_process()
