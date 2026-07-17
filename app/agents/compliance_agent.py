from langchain.agents import create_agent
from langchain_core.tools import tool
from dotenv import load_dotenv
from tavily import TavilyClient
from pydantic import BaseModel, Field
from typing import List
import os
from app.tools.tools import (
    regulatory_vector_search_tool,
    regulatory_hybrid_search_tool,
    regulatory_metadata_search_tool,
)
from app.agents.prompts import system_prompt

# load the env variables
load_dotenv()


from pydantic import BaseModel, Field
from typing import List, Optional


class Citation(BaseModel):
    """Source citation for the generated answer."""

    document: str = Field(description="Source document")
    page: Optional[int] = Field(
        default=None,
        description="Page number if available",
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Source document URL if available",
    )


class ComplianceResponse(BaseModel):
    """Structured response for the Regulatory Compliance Intelligence System."""

    query: str = Field(description="The user's compliance question")
    answer: str = Field(
        description="Grounded answer generated from retrieved regulatory clauses"
    )
    citations: List[Citation] = Field(description="Supporting regulatory citations")
    rule_summary: List[str] = Field(
        description="Key rules, thresholds, limits, or obligations extracted from the regulations"
    )
    input_tokens: Optional[int] = Field(
        default=None, description="Number of input/prompt tokens consumed"
    )
    output_tokens: Optional[int] = Field(
        default=None, description="Number of output/completion tokens consumed"
    )
    total_tokens: Optional[int] = Field(
        default=None, description="Total tokens consumed"
    )
    disclaimer: str = Field(
        description="This response is based on retrieved regulatory documents uploaded"
    )


compliance_agent = create_agent(
    model="openai:gpt-5.5",
    tools=[
        regulatory_vector_search_tool,
        regulatory_hybrid_search_tool,
        regulatory_metadata_search_tool,
    ],
    response_format=ComplianceResponse,
    system_prompt=system_prompt,
)


response = compliance_agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Hi",
            }
        ]
    }
)

agent_response: ComplianceResponse = response["structured_response"]

# print(agent_response)  # pydantic format of the structure response

usage = response["messages"][-1].usage_metadata

agent_response.input_tokens = usage.get("input_tokens")
agent_response.output_tokens = usage.get("output_tokens")
agent_response.total_tokens = usage.get("total_tokens")
# if you only json format
print(agent_response.model_dump_json(indent=2))
