from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.chart_service import chart_url_from_path, create_chart
import logging

logger = logging.getLogger("statbotpro.routes.generate_chart")

class ChartRequest(BaseModel):
    filename: str = Field(..., description="CSV filename in uploads directory")
    chart_type: str = Field(..., description="Chart type: line, bar, pie")
    x_col: str = Field(..., description="Column for X axis or labels")
    y_col: str = Field(..., description="Column for Y axis or values")
    title: str = Field("Chart", description="Chart title")

router = APIRouter()

@router.post("/generate-chart", summary="Generate chart from CSV", tags=["Chart"])
def generate_chart_api(request: ChartRequest):
    try:
        chart_path = create_chart(request.filename, request.chart_type, request.x_col, request.y_col, request.title)
        return {"chart_path": chart_path, "chart_url": chart_url_from_path(chart_path)}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
