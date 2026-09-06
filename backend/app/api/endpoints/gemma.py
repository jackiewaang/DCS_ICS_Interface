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


@router.post("/inference")
async def run_gemma_inference(
    sections: GemmaInferenceSections,
    user_id: UUID = Header(alias="X-User-ID"),
):
    request_id = str(uuid4())
    started_at = time.monotonic()
    logger.info(
        "Gemma inference request started request_id=%s user_id=%s",
        request_id,
        user_id,
    )

    if not any((sections.summary.strip(), sections.research.strip(), sections.impact.strip())):
        raise HTTPException(status_code=422, detail="At least one REF section is required.")

    try:
        result = await gemma_service.run_inference(
            sections.model_dump(),
            request_id=request_id,
        )
        _log_inference(user_id, sections, result)
        logger.info(
            "Gemma inference request completed request_id=%s elapsed_seconds=%.2f",
            request_id,
            time.monotonic() - started_at,
        )
        return result
    except Exception as exc:
        logger.exception(
            "Gemma inference request failed request_id=%s elapsed_seconds=%.2f error_type=%s",
            request_id,
            time.monotonic() - started_at,
            type(exc).__name__,
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
