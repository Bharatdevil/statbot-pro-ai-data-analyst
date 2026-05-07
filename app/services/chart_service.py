import os
import logging
from fastapi import HTTPException, status
from app.utils.csv_utils import load_csv_safe
from app.ai.chart_generator import generate_chart

logger = logging.getLogger("statbotpro.services.chart_service")
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'uploads'))


def chart_url_from_path(chart_path: str) -> str:
    return f"/charts/{os.path.basename(chart_path)}"


def create_chart(filename: str, chart_type: str, x_col: str, y_col: str, title: str) -> str:
    filename = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        logger.warning("File not found: %s", file_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    try:
        df = load_csv_safe(file_path)
    except Exception as e:
        logger.error("Failed to load CSV: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid CSV: {e}")
    try:
        chart_path = generate_chart(df, chart_type, x_col, y_col, title)
    except Exception as e:
        logger.error("Chart generation failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Chart generation failed: {e}")
    return chart_path
