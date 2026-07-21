from langchain.agents import create_agent
from langchain_core.tools import tool
from dotenv import load_dotenv
from tavily import TavilyClient
from pydantic import BaseModel, Field
from typing import List
import os
from app.tools.tools import (
    vector_search_tool,
    hybrid_search_tool,
    metadata_search_tool,
)
from app.agents.prompts import system_prompt

# load the env variables
load_dotenv()


from pydantic import BaseModel, Field
from typing import List, Optional


class QueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None


class Citation(BaseModel):
    """Source citation for the generated answer."""

    document: str = Field(description="Source document")
    page: Optional[int] = Field(
        default=None,
        description="Page number if available",
    )


class ComplianceResponse(BaseModel):
    """Structured response for the Regulatory Compliance Intelligence System."""

    query: str = Field(description="The user's compliance question")
    answer: str = Field(
        description="A concise, directly grounded answer to the user's question based only on the retrieved regulations."
    )
    citations: List[Citation] = Field(description="Supporting regulatory citations")


compliance_agent = create_agent(
    model="openai:gpt-5.5",
    tools=[
        vector_search_tool,
        hybrid_search_tool,
        metadata_search_tool,
    ],
    response_format=ComplianceResponse,
    system_prompt=system_prompt,
)
