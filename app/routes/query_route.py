from fastapi import APIRouter, HTTPException
from app.services.query_service import process_query
from app.agents.compliance_agent import (
    QueryRequest,
    ComplianceResponse,
)

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance Query"])


@router.post("/query", response_model=ComplianceResponse)
async def query_compliance(request: QueryRequest):

    try:
        result = process_query(request)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
