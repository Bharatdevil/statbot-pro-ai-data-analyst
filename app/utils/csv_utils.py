import os
import pandas as pd
from typing import Any

def load_csv_safe(file_path: str) -> pd.DataFrame:
    """
    Safely load a CSV file using pandas. Raises ValueError on failure.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Failed to load CSV: {e}")
