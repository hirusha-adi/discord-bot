import os
import time
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.announcement_dispatch import (
    ensure_announcement_module_enabled,
    send_announcement_to_discord,
    scheduled_announcement_to_request,
)
from app.db import SessionLocal
from app.models import ScheduledAnnouncement

POLL_INTERVAL_SECONDS = int(os.getenv("ANNOUNCEMENT_WORKER_POLL_SECONDS", "5"))
BATCH_SIZE = int(os.getenv("ANNOUNCEMENT_WORKER_BATCH_SIZE", "25"))


def process_once() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        pending_ids = (
            db.execute(
                select(ScheduledAnnouncement.id)
                .where(
                    ScheduledAnnouncement.status == "pending",
                    ScheduledAnnouncement.scheduled_at <= now,
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
                else:
                    # Minimal Stage 9 retry strategy: no automatic retries yet; failures are tracked persistently.
                    announcement.status = "failed"
                    announcement.failure_reason = error or "Unknown error"
            except Exception as exc:  # noqa: BLE001
                announcement.status = "failed"
                announcement.failure_reason = str(exc)

            db.commit()


def main() -> None:
    print("[worker] Announcement worker started")
    while True:
        try:
            process_once()
        except Exception as exc:  # noqa: BLE001
            print(f"[worker] Announcement worker loop error: {exc}")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
