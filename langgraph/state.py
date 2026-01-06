from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """
    The state of the Raava multi-agent luxury automotive system.

    Tracks conversation progress through selection → details → booking → confirmation phases.
    """

    # Conversation messages between client and agents
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Next agent to route to (determined by supervisor)
    next_agent: str

    conversation_phase: str  # "selection", "details", "booking", "confirmation"
    selected_car: str  # Car model selected by user (e.g., "hybrid Urus SE")

    booking_data: dict  # {customer_name, customer_email, customer_phone, booking_type, start_date, end_date, notes}
    order_id: str  # MongoDB order ID after successful booking
