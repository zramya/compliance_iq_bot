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

    # Generate trace id
    result.langsmith_trace_id = str(uuid.uuid4())

    # Token usage
    ai_message = response["messages"][-1]

    usage = ai_message.usage_metadata

    if usage:
        result.input_tokens = usage.get("input_tokens")
        result.output_tokens = usage.get("output_tokens")
        result.total_tokens = usage.get("total_tokens")

    return result
