from fastapi import APIRouter, HTTPException
from app.services.dataset_service import get_dataset_info

router = APIRouter()

@router.get("/dataset-info/{filename}", summary="Get dataset info", tags=["Dataset Info"])
def dataset_info(filename: str):
    """
    Get info about a CSV dataset: rows, columns, column names, shape, and preview.
    """
    try:
        return get_dataset_info(filename)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
