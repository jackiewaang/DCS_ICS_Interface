from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.repositories.feedback_repository import create_feedback

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackCreate(BaseModel):
    tool_usefulness: int = Field(ge=1, le=5)
    score_reasonability: int = Field(ge=1, le=5)
    ease_of_use: int = Field(ge=1, le=5)
    identified_improvements: Literal["yes", "somewhat", "no"]
    comments: str | None = Field(default=None, max_length=5000)

    @field_validator("comments")
    @classmethod
    def validate_comments(cls, value: str | None) -> str | None:
        comments = value.strip() if value else ""
        return comments or None


class FeedbackResponse(BaseModel):
    feedback_id: int
    tool_usefulness: int
    score_reasonability: int
    ease_of_use: int
    identified_improvements: Literal["yes", "somewhat", "no"]
    comments: str | None
    created_at: datetime


@router.post("/", response_model=FeedbackResponse, status_code=201)
def submit_feedback(payload: FeedbackCreate):
    return create_feedback(**payload.model_dump())
