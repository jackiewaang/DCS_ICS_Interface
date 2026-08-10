import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException

from app.database.seed_inferences import (
    seed_ref2014_inferences,
    seed_ref2021_inferences,
)
from app.database.seed_past_cases import (
    seed_ref2014_past_cases,
    seed_ref2021_past_cases,
)
from app.database.session import SessionLocal


router = APIRouter(prefix="/api/seeding", tags=["Seeding"])

SUPPORTED_REF_YEARS = {2014, 2021}
_running_seed_tasks: dict[int, asyncio.Task] = {}


@router.post("/ref/{ref_year}")
async def seed_ref_year(ref_year: int):
    if ref_year not in SUPPORTED_REF_YEARS:
        raise HTTPException(status_code=400, detail=f"Unsupported REF year: {ref_year}")

    existing_task = _running_seed_tasks.get(ref_year)
    if existing_task is not None and not existing_task.done():
        return {
            "ref_year": ref_year,
            "status": "already_running",
        }

    _running_seed_tasks[ref_year] = asyncio.create_task(_run_ref_year_seed(ref_year))
    return {
        "ref_year": ref_year,
        "status": "scheduled",
    }


async def _run_ref_year_seed(ref_year: int) -> None:
    try:
        result = await asyncio.to_thread(_seed_ref_year_sync, ref_year)
        print(f"Seeded REF{ref_year}: {result}")
    except Exception as exc:
        print(f"Failed to seed REF{ref_year}: {exc}")


def _seed_ref_year_sync(ref_year: int) -> dict[str, Any]:
    case_seeders = {
        2014: seed_ref2014_past_cases,
        2021: seed_ref2021_past_cases,
    }
    inference_seeders = {
        2014: seed_ref2014_inferences,
        2021: seed_ref2021_inferences,
    }

    with SessionLocal() as db:
        try:
            case_count = case_seeders[ref_year](db=db)
            db.flush()
            inference_totals = inference_seeders[ref_year](db=db)
            db.commit()
            return {
                "past_cases": case_count,
                "inferences": inference_totals,
            }
        except Exception:
            db.rollback()
            raise
