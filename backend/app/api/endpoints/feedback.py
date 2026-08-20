from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.repositories.feedback_repository import create_feedback

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    message: str = Field(min_length=1, max_length=5000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("Feedback message cannot be empty")
        return message


class FeedbackResponse(BaseModel):
    feedback_id: int
    rating: int
    message: str
    created_at: datetime


@router.post("/", response_model=FeedbackResponse, status_code=201)
def submit_feedback(payload: FeedbackCreate):
    return create_feedback(rating=payload.rating, message=payload.message)
