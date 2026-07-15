from sqlalchemy import Float, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Unique Ref+Case ID for past ICS, NULL for new inferences
    case_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    ref_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    institution: Mapped[str | None] = mapped_column(Text, nullable=True)
    uoa: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, default="draft", nullable=True)

    # Ground truth for past ICS, NULL for new inferences
    gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_label: Mapped[int | None] = mapped_column(Integer, nullable=True) # 1 for High, 0 for Low
    
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    features = relationship(
        "DocumentFeatures",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan"
        )
    inferences = relationship(
        "Inference",
        back_populates="document",
        cascade="all, delete-orphan",
    )

class DocumentFeatures(Base):
    __tablename__ = "document_features"

    feature_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document_metadata.document_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    features_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    entities_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # READABILITY METRICS
    flesch_reading_ease: Mapped[float | None] = mapped_column(Float, nullable=True)
    dale_chall_readability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    smog_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    automated_readability_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # SENTIMENT ANALYSIS
    sentiment_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_10th: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_50th: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_75th: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_90th: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # OTHER TEXTUAL FEATURES
    word_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    paragraph_count: Mapped[float | None] = mapped_column(Float, nullable=True)

    # NAMED ENTITY VALUES
    person_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    norp_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    fac_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    org_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    gpe_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    loc_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    product_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    event_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    work_of_art_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    law_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    language_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    date_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    time_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    percent_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    money_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    quantity_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    ordinal_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)
    cardinal_entities: Mapped[list[str] | None] = mapped_column(JSON, default=list, nullable=True)

    document: Mapped[DocumentMetadata] = relationship(back_populates="features")
