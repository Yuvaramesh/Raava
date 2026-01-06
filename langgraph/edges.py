from typing import Literal


def router(state) -> Literal["concierge", "service_manager", "consigner", "__end__"]:
    """
    Routes to the next specialist agent based on the supervisor's decision.

    The supervisor analyzes the client's inquiry and determines which
    specialist is best suited to handle the request:

    - concierge: Vehicle acquisition, financing, marketplace guidance
    - service_manager: Maintenance, repairs, service coordination
    - consigner: Vehicle listings, valuations, market strategy
    - __end__: Supervisor handled the inquiry directly

    Returns:
        The name of the next agent to invoke, or "__end__" to complete
    """
    next_agent = state.get("next_agent", "__end__")

    # Ensure valid routing
    valid_agents = ["concierge", "service_manager", "consigner", "__end__"]
    if next_agent not in valid_agents:
        # Default to end if invalid routing
        return "__end__"

    return next_agent
