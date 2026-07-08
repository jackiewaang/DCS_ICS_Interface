from app.database import SessionLocal
from app.models.document import DocumentMetadata


def document_payload(document: DocumentMetadata) -> dict:
    return {
        "document_id": document.document_id,
        "case_id": document.case_id,
        "title": document.title,
        "institution": document.institution,
        "uoa": document.uoa,
        "status": document.status,
        "ref_year": document.ref_year,
        "gpa": document.gpa,
        "impact_label": document.impact_label,
        "raw_text": document.raw_text,
        "sections": {
            "summary": document.summary_text or "",
            "research": document.research_text or "",
            "impact": document.impact_text or "",
        },
    }


def create_draft_case(filename: str, sections: dict[str, str], raw_text: str | None = None) -> dict:
    with SessionLocal() as db:
        document = DocumentMetadata(
            title=filename,
            status="draft",
            raw_text=raw_text or "\n\n".join(
                section
                for section in (
                    sections.get("summary", ""),
                    sections.get("research", ""),
                    sections.get("impact", ""),
                )
                if section
            ),
            summary_text=sections.get("summary", ""),
            research_text=sections.get("research", ""),
            impact_text=sections.get("impact", ""),
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        return document_payload(document)
