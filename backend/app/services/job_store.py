import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import uuid4


JOB_RETENTION_SECONDS = 3600


class JobNotFound(Exception):
    pass


class JobForbidden(Exception):
    pass


@dataclass
class JobRecord:
    owner_id: str
    status: str = "pending"
    result: object | None = None
    error: str | None = None
    finished_at: float | None = None


class JobStore:
    """Small in-memory store for background inference jobs."""

    def __init__(self):
        self._jobs: dict[str, JobRecord] = {}
        self._tasks: set[asyncio.Task] = set()

    def submit(
        self,
        owner_id: str,
        work: Callable[[], Awaitable[object]],
    ) -> str:
        self._remove_expired_jobs()
        job_id = str(uuid4())
        self._jobs[job_id] = JobRecord(owner_id=owner_id)
        task = asyncio.create_task(self._run(job_id, work))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job_id

    def get(self, job_id: str, owner_id: str) -> JobRecord:
        self._remove_expired_jobs()
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFound
        if job.owner_id != owner_id:
            raise JobForbidden
        return job

    async def _run(
        self,
        job_id: str,
        work: Callable[[], Awaitable[object]],
    ) -> None:
        job = self._jobs[job_id]
        job.status = "running"
        try:
            job.result = await work()
            job.status = "completed"
        except Exception as exc:
            job.error = str(exc) or type(exc).__name__
            job.status = "failed"
        finally:
            job.finished_at = time.monotonic()

    def _remove_expired_jobs(self) -> None:
        cutoff = time.monotonic() - JOB_RETENTION_SECONDS
        expired_ids = [
            job_id
            for job_id, job in self._jobs.items()
            if job.finished_at is not None and job.finished_at < cutoff
        ]
        for job_id in expired_ids:
            del self._jobs[job_id]


job_store = JobStore()
