import os
from typing import Dict, Any
from fastapi import HTTPException, status
from app.utils.csv_utils import load_csv_safe

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'uploads'))

def get_dataset_info(filename: str) -> Dict[str, Any]:
    """
    Load a CSV file and return dataset info for API response.
    """
    filename = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    try:
        df = load_csv_safe(file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pandas error: {e}")
    columns = list(df.columns)
    preview = df.head(5).to_dict(orient="records")
    return {
        "filename": filename,
        "rows": len(df),
        "columns_count": len(columns),
        "columns": columns,
        "shape": list(df.shape),
        "preview": preview
    }
