import os
import logging
from fastapi import UploadFile
from app.utils.file_utils import save_upload_file

logger = logging.getLogger("statbotpro.services.upload_service")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'uploads')
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)


async def handle_csv_upload(file: UploadFile) -> dict[str, str]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    await save_upload_file(file, file_path)
    logger.info("CSV uploaded and set active: %s", filename)
    return {"filename": filename, "message": "Upload successful"}
