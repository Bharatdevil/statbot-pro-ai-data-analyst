from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.analyze_service import analyze_dataset
import logging

logger = logging.getLogger("statbotpro.routes.analyze")

class AnalyzeRequest(BaseModel):
    filename: str = Field(..., description="CSV filename in uploads directory")
    query: str = Field(..., description="Natural language question about the dataset")

router = APIRouter()

@router.post("/analyze", summary="AI-powered CSV analysis", tags=["AI Analysis"])
def analyze(request: AnalyzeRequest):
    """
    Analyze a CSV file using Gemini and LangChain DataFrame Agent.
    """
    try:
        return analyze_dataset(request.filename, request.query)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
