from app.database import SessionLocal
from app.models.feedback import Feedback


def create_feedback(rating: int, message: str) -> dict:
    with SessionLocal() as db:
        feedback = Feedback(rating=rating, message=message)
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return {
            "feedback_id": feedback.feedback_id,
            "rating": feedback.rating,
            "message": feedback.message,
            "created_at": feedback.created_at,
        }
