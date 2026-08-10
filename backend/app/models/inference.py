from typing import Any, Dict
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LLMInferenceStatus(str, Enum):
    RUNNING = "running"
    ERROR = "error"
    COMPLETED = "completed"


class ModelConfig(Base):
    __tablename__ = "model_configs"

    config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    
    # Model Architecture
    emb_model: Mapped[str | None] = mapped_column(String, nullable=True) # e.g. Qwen3-Embedding-4B
    run_mode: Mapped[str | None] = mapped_column(String, nullable=True) # 'classification' or 'regression'
    fusion_type: Mapped[str | None] = mapped_column(Text, default="gated", nullable=True)
    normalise_emb: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    normalise_case_feats: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    label_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Paths
    model_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    scaler_path: Mapped[str | None] = mapped_column(String, nullable=True)

    # architecture: Mapped[str | None] = mapped_column(String, nullable=True)
    # model_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    # scaler_path: Mapped[str | None] = mapped_column(String, nullable=True)
    # embedding_name: Mapped[str | None] = mapped_column(String, nullable=True)
    # input_dim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # feature_dim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # hidden_dim: Mapped[int | None] = mapped_column(Integer, default=128, nullable=True)
    # input_granularity: Mapped[str | None] = mapped_column(Text, nullable=True)
    # task: Mapped[str | None] = mapped_column(Text, nullable=True)
    # global_importance_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    # case_attribution_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    # use_features: Mapped[int | None] = mapped_column(Integer, nullable=True)

    inferences = relationship(
        "Inference",
        back_populates="model_config",
        cascade="all, delete-orphan",
    )
    feature_importances = relationship(
        "ModelFeatureImportance",
        back_populates="model_config",
        cascade="all, delete-orphan",
    )


class ModelFeatureImportance(Base):
    __tablename__ = "model_feature_importances"
    __table_args__ = (
        UniqueConstraint("config_id", "feature_name", name="uq_model_feature_importance"),
    )

    importance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(
        ForeignKey("model_configs.config_id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_name: Mapped[str] = mapped_column(String, nullable=False)
    mean_permutation_importance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    model_config: Mapped[ModelConfig] = relationship(back_populates="feature_importances")


class Inference(Base):
    __tablename__ = "inferences"

    inference_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document_metadata.document_id", ondelete="CASCADE"),
        nullable=False,
    )
    config_id: Mapped[int] = mapped_column(
        ForeignKey("model_configs.config_id", ondelete="CASCADE"),
        nullable=False,
    )

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    true_label: Mapped[float | None] = mapped_column(Float, nullable=True)
    prediction_label: Mapped[str | None] = mapped_column(String, nullable=True) # High or Low
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    
    narrative_contribution: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_contribution: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_attributions: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("DocumentMetadata", back_populates="inferences")
    model_config: Mapped[ModelConfig] = relationship(back_populates="inferences")
    attentions = relationship(
        "Attention",
        back_populates="inference",
        cascade="all, delete-orphan",
    )
    llm_inference = relationship(
        "LLMInference",
        back_populates="inference",
        cascade="all, delete-orphan",
        uselist=False,
    )

class LLMInference(Base):
    __tablename__ = "llm_inferences"

    llm_inference_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inference_id: Mapped[int] = mapped_column(
        ForeignKey("inferences.inference_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    significance_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    significance_improvements: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_improvements: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LLMInferenceStatus] = mapped_column(
        SQLEnum(
            LLMInferenceStatus,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            native_enum=False,
            create_constraint=True,
            name="llm_inference_status",
            validate_strings=True,
        ),
        default=LLMInferenceStatus.RUNNING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    inference: Mapped[Inference] = relationship(back_populates="llm_inference")


class Attention(Base):
    __tablename__ = "attentions"

    attention_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inference_id: Mapped[int] = mapped_column(
        ForeignKey("inferences.inference_id", ondelete="CASCADE"),
        nullable=False,
    )
    sentence_text: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)

    inference: Mapped[Inference] = relationship(back_populates="attentions")
