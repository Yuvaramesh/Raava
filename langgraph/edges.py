from typing import Literal


def router(state) -> Literal["concierge", "service_manager", "consigner", "__end__"]:
    """Routes to the next agent based on the state's next_agent field."""
    return state.get("next_agent", "__end__")
