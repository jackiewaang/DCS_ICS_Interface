from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Model Architecture
    emb_model: Mapped[str] = mapped_column(String, nullable=False)  # e.g. Qwen3-Embedding-4B
    run_mode: Mapped[str] = mapped_column(String, nullable=False)  # classification/regression
    fusion_type: Mapped[str] = mapped_column(Text, default="gated", nullable=False)
    case_feat_names: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    feature_importances: Mapped[dict[str, float]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Paths
    model_path: Mapped[str] = mapped_column(Text, nullable=False)
    scaler_path: Mapped[str | None] = mapped_column(String, nullable=True)
