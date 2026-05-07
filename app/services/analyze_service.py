import logging
from typing import Dict, Any
from fastapi import HTTPException, status
from app.utils.csv_utils import load_csv_safe
from app.ai.chart_generator import generate_chart_from_query, query_needs_chart
from app.ai.gemini_agent import analyze_csv_with_gemini
from app.services.chart_service import chart_url_from_path
import os

logger = logging.getLogger("statbotpro.services.analyze_service")
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'uploads'))
UNSAFE_TERMS = ("os.system", "subprocess", "rm -rf", "delete", "shutil", "eval", "exec")


def _is_unsafe_query(query: str) -> bool:
    lowered = query.lower()
    return any(term in lowered for term in UNSAFE_TERMS)


def _run_analysis_with_retry(df, query: str) -> str:
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            return analyze_csv_with_gemini(df, query)
        except Exception as e:
            last_error = e
            logger.warning("AI analysis attempt %s failed: %s", attempt + 1, e)
    raise RuntimeError("AI analysis failed after retry.") from last_error

def analyze_dataset(filename: str, query: str) -> Dict[str, Any]:
    """
    Load CSV, analyze with Gemini agent, optionally generate a chart, and return answer.
    """
    filename = os.path.basename(filename)
    if _is_unsafe_query(query):
        return {"query": query, "answer": "Unsafe operation detected.", "chart_url": None, "dataset": filename}

    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        logger.warning("File not found: %s", file_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    try:
        df = load_csv_safe(file_path)
    except Exception as e:
        logger.error("Failed to load CSV: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid CSV: {e}")

    chart_url = None
    if query_needs_chart(query):
        try:
            chart_path = generate_chart_from_query(df, query, title=query[:70])
            chart_url = chart_url_from_path(chart_path)
        except Exception as e:
            logger.warning("Automatic chart generation failed: %s", e)

    try:
        answer = _run_analysis_with_retry(df, query)
    except Exception as e:
        logger.error("AI analysis failed after retry: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis failed. Please rephrase your question and try again.",
        )
    return {"query": query, "answer": answer, "chart_url": chart_url, "dataset": filename}
