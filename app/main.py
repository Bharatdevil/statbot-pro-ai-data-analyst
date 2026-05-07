import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

from app.routes.upload_csv import router as upload_csv_router
from app.routes.dataset_info import router as dataset_info_router
from app.routes.analyze import router as analyze_router
from app.routes.generate_chart import router as generate_chart_router

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="StatBot Pro", description="AI-powered CSV analysis API.")
app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/health")
def health_check():
    return {"status": "running"}


app.include_router(upload_csv_router)
app.include_router(dataset_info_router)
app.include_router(analyze_router)
app.include_router(generate_chart_router)
