from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(
            "tool_usefulness >= 1 AND tool_usefulness <= 5",
            name="ck_feedback_tool_usefulness",
        ),
        CheckConstraint(
            "score_reasonability >= 1 AND score_reasonability <= 5",
            name="ck_feedback_score_reasonability",
        ),
        CheckConstraint(
            "ease_of_use >= 1 AND ease_of_use <= 5",
            name="ck_feedback_ease_of_use",
        ),
        CheckConstraint(
            "identified_improvements IN ('yes', 'somewhat', 'no')",
            name="ck_feedback_identified_improvements",
        ),
    )

    feedback_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    tool_usefulness: Mapped[int] = mapped_column(Integer, nullable=False)
    score_reasonability: Mapped[int] = mapped_column(Integer, nullable=False)
    ease_of_use: Mapped[int] = mapped_column(Integer, nullable=False)
    identified_improvements: Mapped[str] = mapped_column(String(16), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
