import uuid

from app.agents.compliance_agent import compliance_agent
from app.agents.compliance_agent import (
    QueryRequest,
    ComplianceResponse,
)


def process_query(request: QueryRequest) -> ComplianceResponse:

    response = compliance_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": request.query,
                }
            ]
        }
    )

    result: ComplianceResponse = response["structured_response"]
    return result
