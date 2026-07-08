from fastapi import APIRouter, File, HTTPException, UploadFile
from app import crud
from app.pipeline.document_extractor import document_extractor
from app.repositories.document_repository import create_draft_case

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("/")
def search_cases(q: str = None, uoa: str = None):
    return crud.get_cases(q, uoa)


@router.get("/inference/{inference_id}")
def read_inference(inference_id: int):
    data = crud.get_inference_details(inference_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return data


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
        "sections": sections
    }

    # draft = create_draft_case(filename=filename, sections=sections, raw_text=raw_text)

    # return {
    #     "status": "draft",
    #     "document_id": draft["document_id"],
    #     "title": draft["title"],
    #     "sections": draft["sections"],
    # }


@router.get("/{document_id}")
def read_case(document_id: int):
    case = crud.get_case_by_id(document_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case study not found")
    return case
