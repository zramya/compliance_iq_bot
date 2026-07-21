from fastapi import APIRouter, UploadFile, HTTPException, status
from app.services.upload_service import save_uploaded_pdf
from pathlib import Path

router = APIRouter(prefix="/api/v1/compliance")

# Repository root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# data folder outside app/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Fixed filename
PDF_PATH = DATA_DIR / "compliance.pdf"


# localhost:8000/api/v1/compliance/ingestion
@router.post("/ingestion", status_code=status.HTTP_200_OK)
async def upload_compliance_data(pdf_file: UploadFile):

    if pdf_file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed.",
        )

    result = await save_uploaded_pdf(pdf_file)

    return {"message": "Compliance PDF uploaded successfully.", "data": result}
