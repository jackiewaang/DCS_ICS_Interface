import asyncio
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.database.session import SessionLocal
from app.models.document import DocumentMetadata


# Set this to False to keep user-submitted analyses permanently.
DELETE_USER_ANALYSES_AFTER_TTL = True
USER_ANALYSIS_TTL = timedelta(minutes=2)
CLEANUP_INTERVAL_SECONDS = 60


def user_analysis_expiry() -> datetime | None:
    if not DELETE_USER_ANALYSES_AFTER_TTL:
        return None
    return _utc_now() + USER_ANALYSIS_TTL


def delete_expired_user_analyses() -> int:
    if not DELETE_USER_ANALYSES_AFTER_TTL:
        return 0

    with SessionLocal() as db:
        result = db.execute(
            delete(DocumentMetadata).where(
                DocumentMetadata.case_id.is_(None),
                DocumentMetadata.expires_at.is_not(None),
                DocumentMetadata.expires_at <= _utc_now(),
            )
        )
        db.commit()
        return result.rowcount or 0


def start_cleanup_task() -> asyncio.Task | None:
    if not DELETE_USER_ANALYSES_AFTER_TTL:
        return None
    return asyncio.create_task(_cleanup_loop())


async def stop_cleanup_task(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def _cleanup_loop() -> None:
    while True:
        try:
            delete_expired_user_analyses()
        except Exception as exc:
            print(f"User analysis cleanup failed: {exc}")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
