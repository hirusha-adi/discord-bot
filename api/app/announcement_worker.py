import logging
import os
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.announcement_dispatch import (
    ensure_announcement_module_enabled,
    send_announcement_to_discord,
    scheduled_announcement_to_request,
)
from app.db import SessionLocal
from app.logging_config import configure_logging
from app.models import ScheduledAnnouncement

POLL_INTERVAL_SECONDS = int(os.getenv("ANNOUNCEMENT_WORKER_POLL_SECONDS", "5"))
BATCH_SIZE = int(os.getenv("ANNOUNCEMENT_WORKER_BATCH_SIZE", "25"))
MAX_RETRIES = int(os.getenv("ANNOUNCEMENT_WORKER_MAX_RETRIES", "3"))
BASE_BACKOFF_SECONDS = int(os.getenv("ANNOUNCEMENT_WORKER_BACKOFF_SECONDS", "15"))
logger = logging.getLogger("announcement.worker")


def process_once() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        pending_ids = (
            db.execute(
                select(ScheduledAnnouncement.id)
                .where(
                    ScheduledAnnouncement.status == "pending",
                    ScheduledAnnouncement.scheduled_at <= now,
                    (
                        (ScheduledAnnouncement.next_attempt_at.is_(None))
                        | (ScheduledAnnouncement.next_attempt_at <= now)
                    ),
                )
                .order_by(ScheduledAnnouncement.scheduled_at.asc())
                .limit(BATCH_SIZE)
            )
            .scalars()
            .all()
        )

        for announcement_id in pending_ids:
            claimed = db.execute(
                update(ScheduledAnnouncement)
                .where(
                    ScheduledAnnouncement.id == announcement_id,
                    ScheduledAnnouncement.status == "pending",
                )
                .values(status="in_progress")
            )
            db.commit()
            if claimed.rowcount == 0:
                continue

            announcement = db.execute(
                select(ScheduledAnnouncement).where(ScheduledAnnouncement.id == announcement_id)
            ).scalar_one_or_none()
            if announcement is None:
                continue

            try:
                ensure_announcement_module_enabled(db, announcement.guild_id)
                request = scheduled_announcement_to_request(db, announcement)
                success, error = send_announcement_to_discord(request)

                if success:
                    announcement.status = "sent"
                    announcement.sent_at = datetime.now(UTC)
                    announcement.failure_reason = None
                    announcement.next_attempt_at = None
                else:
                    retry_count = int(announcement.retry_count or 0) + 1
                    if retry_count <= MAX_RETRIES:
                        backoff_seconds = BASE_BACKOFF_SECONDS * (2 ** (retry_count - 1))
                        announcement.status = "pending"
                        announcement.retry_count = retry_count
                        announcement.next_attempt_at = datetime.now(UTC).replace(
                            microsecond=0
                        ) + timedelta(seconds=backoff_seconds)
                        announcement.failure_reason = error or "Retry scheduled"
                        logger.warning(
                            "announcement_retry_scheduled id=%s retry_count=%s max_retries=%s backoff_seconds=%s",
                            announcement.id,
                            retry_count,
                            MAX_RETRIES,
                            backoff_seconds,
                        )
                    else:
                        announcement.status = "failed"
                        announcement.retry_count = retry_count
                        announcement.failure_reason = error or "Unknown error"
            except Exception as exc:  # noqa: BLE001
                retry_count = int(announcement.retry_count or 0) + 1
                if retry_count <= MAX_RETRIES:
                    backoff_seconds = BASE_BACKOFF_SECONDS * (2 ** (retry_count - 1))
                    announcement.status = "pending"
                    announcement.retry_count = retry_count
                    announcement.next_attempt_at = datetime.now(UTC).replace(microsecond=0) + timedelta(
                        seconds=backoff_seconds
                    )
                    announcement.failure_reason = str(exc)
                    logger.exception(
                        "announcement_retry_exception id=%s retry_count=%s max_retries=%s",
                        announcement.id,
                        retry_count,
                        MAX_RETRIES,
                    )
                else:
                    announcement.status = "failed"
                    announcement.retry_count = retry_count
                    announcement.failure_reason = str(exc)
                    logger.exception(
                        "announcement_failed_exception id=%s retry_count=%s max_retries=%s",
                        announcement.id,
                        retry_count,
                        MAX_RETRIES,
                    )

            db.commit()


def main() -> None:
    configure_logging("worker")
    logger.info("announcement_worker_started poll_interval_seconds=%s batch_size=%s", POLL_INTERVAL_SECONDS, BATCH_SIZE)
    while True:
        try:
            process_once()
        except Exception as exc:  # noqa: BLE001
            logger.exception("announcement_worker_loop_error error=%s", exc)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
