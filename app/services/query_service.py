from app.agents.compliance_agent import compliance_agent
from app.agents.compliance_agent import (
    QueryRequest,
    ComplianceResponse,
)


def process_query(request: QueryRequest) -> ComplianceResponse:
    messages = []

    for message in request.chat_history:
        messages.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )

    messages.append(
        {
            "role": "user",
            "content": request.query,
        }
    )

    response = compliance_agent.invoke(
        {
            "messages": messages,
        },
        config={
            "configurable": {
                "thread_id": request.thread_id,
            }
        },
    )

    result: ComplianceResponse = response["structured_response"]

    return result
