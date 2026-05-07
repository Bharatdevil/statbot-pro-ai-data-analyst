import os
from fastapi import UploadFile


def is_file_exists(file_path: str) -> bool:
    """
    Check if a file already exists at the given path.
    """
    return os.path.exists(file_path)


async def save_upload_file(upload_file: UploadFile, destination: str):
    """
    Save the uploaded file to the destination path.
    """
    with open(destination, "wb") as buffer:
        while True:
            chunk = await upload_file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            buffer.write(chunk)
