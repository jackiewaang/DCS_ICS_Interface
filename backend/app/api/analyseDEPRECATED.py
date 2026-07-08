from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.utils import convert_bytes_to_text
from app.pipeline.feature_extraction import clean_text, run_extraction
from app.pipeline.generate_embeddings import embedding_engine
from app.services.inference_service import inference_engine
from app.database import get_model_config, list_model_configs
from app.services.utils import get_ref_sections
from app.crud import create_inference_case

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.post("/run")
async def analyse_document(config_id, file: UploadFile = File(...)):

    config = get_model_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    
    ext = file.filename.split(".")[-1].lower()
    content = await file.read()
    raw_text = convert_bytes_to_text(content, ext)

    if not raw_text:
        raise HTTPException(status_code=400, detail="Unsupported file type or empty content")

    sections = get_ref_sections(raw_text)

    f_text = sections.get("feature_text") if isinstance(sections, dict) else raw_text
    e_text = sections.get("embedding_text") if isinstance(sections, dict) else raw_text

    f_text = f_text or raw_text
    e_text = e_text or raw_text

    try:
        ordered_features = None
        ui_features = {}

        if config['use_features'] == 1:
            ui_features, ordered_features = run_extraction(clean_text(f_text))
        
        sentences, vectors = embedding_engine.run_embedding_inference(
            clean_text(e_text),
            model_name=config['embedding_name'],
            granularity=config['input_granularity']
        )

        results = inference_engine.run_inference(config, vectors, ordered_features)

        # Extract metadata from the processed features
        inst = ui_features.get("institution", "Unknown Institution")
        uoa = ui_features.get("uoa", "Unknown UoA")

        # Map the prediction for the CRUD function
        doc_id = create_inference_case(
            filename=file.filename,
            features=ui_features, 
            sentences=sentences,
            prediction=results, 
            institution=inst,
            uoa=uoa,
            config_id=int(config_id)
        )

        return {
            "status": "success",
            "document_id": doc_id,
            "results": {
                "score": results["score"],
                "label": results["label"],
                "heatmap": results["attention"],
                # Add these so the frontend can render the charts immediately
                "narrative_contribution": results.get("narrative_contribution"),
                "feature_contribution": results.get("feature_contribution"),
                "feature_gates": results.get("feature_gates")
            },
            "writing_stats": ui_features,
            "sentences": sentences
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs")
def list_configs():
    """
    Fetches all available model configurations for the frontend sidebar.
    """
    try:
        return [
            {
                "config_id": config["config_id"],
                "name": config["name"],
                "architecture": config["architecture"],
                "use_features": config["use_features"],
                "input_granularity": config["input_granularity"],
            }
            for config in list_model_configs()
        ]
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve model configurations.")
