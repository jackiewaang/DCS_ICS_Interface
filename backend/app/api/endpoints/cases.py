from fastapi import APIRouter, File, HTTPException, UploadFile

from app.pipeline.document_extractor import document_extractor

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.post("/upload")
async def upload_case(file: UploadFile = File(...)):
    filename = file.filename or "Untitled case"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty")

    try:
        raw_text = document_extractor.extract_pdf_text(pdf_bytes)
        sections = document_extractor.split_ref_sections(raw_text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not extract PDF text: {exc}") from exc

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in PDF")

    if not any(sections.values()):
        raise HTTPException(status_code=400, detail="Could not identify REF sections in PDF")

    return {
        "title": filename,
        "sections": sections,
    }
