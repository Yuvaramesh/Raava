import os
from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Router(BaseModel):
    """Router for the multi-agent system."""

    next_agent: Literal["concierge", "service_manager", "consigner", "__end__"] = Field(
        description="The next agent to route to, or '__end__' if the request is complete."
    )


def get_supervisor_agent():
    """Returns a supervisor agent that routes user queries to specialized agents."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite", google_api_key=os.getenv("GEMINI_API_KEY")
    )

    # We use structured output to ensure the LLM returns a valid next_agent
    structured_llm = llm.with_structured_output(Router)

    system_prompt = """You are a highly intelligent supervisor for a luxury automotive assistant named Raava.
    Your job is to route user requests to the appropriate specialized agent.

    Specialized Agents:
    1. concierge: Buying, marketplace matching, financing (PCP/HP), and buyer-seller facilitation.
    2. service_manager: Routine check-ups, maintenance guidance, upgrades, and booking.
    3. consigner: Listing cars, photography, valuations, and marketplace strategy.

    INSTRUCTIONS:
    - Route accurately to the correct agent.
    - If you handle a general query yourself, be brief and end with: "[Replied by: Supervisor Agent]"
    """

    return structured_llm, system_prompt
