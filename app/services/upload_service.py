from pathlib import Path
import shutil
from fastapi import UploadFile
from app.ingestion.ingestion import ingest_pdf


async def save_uploaded_pdf(uploaded_file: UploadFile):

    # Repository root
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    # data folder outside app/
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)

    # Fixed filename
    PDF_PATH = DATA_DIR / "compliance.pdf"

    with PDF_PATH.open("wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)
    print(f"Saved uploaded PDF to: {PDF_PATH}")
    ingest_pdf(PDF_PATH)  # Call the ingest_pdf function with the saved PDF path
    return PDF_PATH
