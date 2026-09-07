import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.clients.slurm_client import SlurmClient
from app.services.gemma_service import GemmaService
from app.services.job_store import JobForbidden, JobNotFound, job_store


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/gemma", tags=["Gemma"])
gemma_service = GemmaService(slurm_client=SlurmClient())
REPO_ROOT = Path(__file__).resolve().parents[4]
LOGS_DIR = REPO_ROOT / "logs-users"


class GemmaInferenceSections(BaseModel):
    title: str = "Untitled inference"
    summary: str = ""
    research: str = ""
    impact: str = ""


@router.post("/jobs", status_code=202)
async def submit_gemma_job(
    sections: GemmaInferenceSections,
    user_id: UUID = Header(alias="X-User-ID"),
):
    request_id = str(uuid4())
    logger.info(
        "Gemma inference request accepted request_id=%s user_id=%s",
        request_id,
        user_id,
    )

    if not any((sections.summary.strip(), sections.research.strip(), sections.impact.strip())):
        raise HTTPException(status_code=422, detail="At least one REF section is required.")

    job_id = job_store.submit(
        str(user_id),
        lambda: _run_gemma_job(request_id, user_id, sections),
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}")
async def get_gemma_job(
    job_id: str,
    user_id: UUID = Header(alias="X-User-ID"),
):
    try:
        job = job_store.get(job_id, str(user_id))
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail="Gemma job not found.") from exc
    except JobForbidden as exc:
        raise HTTPException(status_code=403, detail="This Gemma job belongs to another user.") from exc

    response = {"job_id": job_id, "status": job.status}
    if job.status == "completed":
        response["result"] = job.result
    elif job.status == "failed":
        response["error"] = job.error
    return response


async def _run_gemma_job(
    request_id: str,
    user_id: UUID,
    sections: GemmaInferenceSections,
) -> dict:
    started_at = time.monotonic()
    try:
        result = await gemma_service.run_inference(
            sections.model_dump(),
            request_id=request_id,
        )
        _log_inference(user_id, sections, result)
        logger.info(
            "Gemma inference job completed request_id=%s elapsed_seconds=%.2f",
            request_id,
            time.monotonic() - started_at,
        )
        return result
    except Exception:
        logger.exception(
            "Gemma inference job failed request_id=%s elapsed_seconds=%.2f",
            request_id,
            time.monotonic() - started_at,
        )
        raise


def _log_inference(
    user_id: UUID,
    sections: GemmaInferenceSections,
    result: dict,
) -> None:
    user_dir = LOGS_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": result["model_name"],
        "inputs": {
            "title": sections.title,
            "summary": sections.summary,
            "research": sections.research,
            "impact": sections.impact,
        },
        "output": {
            "prediction_score": result["score"],
            "comments": result["comments"],
        },
    }
    with (user_dir / "gemma_inferences.jsonl").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
