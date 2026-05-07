from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.services.upload_service import handle_csv_upload

router = APIRouter()

@router.post("/upload-csv", summary="Upload a CSV file", tags=["CSV Upload"])
async def upload_csv(file: UploadFile = File(...)):
    """
    Endpoint to upload a CSV file. Only .csv files are accepted.
    """
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv files are allowed.")
    result = await handle_csv_upload(file)
    return result
