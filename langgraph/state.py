from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """
    The state of the Raava multi-agent luxury automotive system.

    This state is passed between agents and tracks the conversation
    and routing decisions.
    """

    # Conversation messages between client and agents
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Next agent to route to (determined by supervisor)
    next_agent: str
