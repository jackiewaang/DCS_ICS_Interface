from fastapi import APIRouter, HTTPException, Query
from app import crud

router = APIRouter(prefix="/api/cases", tags=["Cases"])

@router.get("/")
def search_cases(q: str = None, uoa: str = None):
    # This returns the list for your dashboard table
    return crud.get_cases(q, uoa)

@router.get("/{document_id}")
def read_case(document_id: int):
    # This returns the full detail for the expanded view/modal
    case = crud.get_case_by_id(document_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case study not found")
    return case

@router.get("/inference/{inference_id}")
def read_inference(inference_id: int):
    # Call the new inference-specific CRUD function
    data = crud.get_inference_details(inference_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return data