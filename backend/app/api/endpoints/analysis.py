from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.database import SessionLocal
from app.models.inference import ModelConfig
from app.pipeline.manager import PipelineManager

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])
pipeline_manager = PipelineManager()


class InferenceSections(BaseModel):
    summary: str = ""
    research: str = ""
    impact: str = ""


@router.get("/models")
def list_models():
    with SessionLocal() as db:
        models = db.scalars(
            select(ModelConfig).order_by(ModelConfig.config_id)
        ).all()

        return [
            {
                column.name: getattr(model, column.name)
                for column in ModelConfig.__table__.columns
            }
            for model in models
        ]


@router.post("/inference")
async def run_inference(config_id: int, sections: InferenceSections):
    output = pipeline_manager.run_inference(
        sections.model_dump(),
        config_id=config_id,
    )

    return output
