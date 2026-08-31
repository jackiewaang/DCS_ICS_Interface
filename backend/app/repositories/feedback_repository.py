from app.database import SessionLocal
from app.models.feedback import Feedback


def create_feedback(
    tool_usefulness: int,
    score_reasonability: int,
    ease_of_use: int,
    identified_improvements: str,
    comments: str | None,
) -> dict:
    with SessionLocal() as db:
        feedback = Feedback(
            tool_usefulness=tool_usefulness,
            score_reasonability=score_reasonability,
            ease_of_use=ease_of_use,
            identified_improvements=identified_improvements,
            comments=comments,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return {
            "feedback_id": feedback.feedback_id,
            "tool_usefulness": feedback.tool_usefulness,
            "score_reasonability": feedback.score_reasonability,
            "ease_of_use": feedback.ease_of_use,
            "identified_improvements": feedback.identified_improvements,
            "comments": feedback.comments,
            "created_at": feedback.created_at,
        }
