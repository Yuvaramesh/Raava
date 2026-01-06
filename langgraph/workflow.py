from langgraph.graph import StateGraph, END
from langgraph.state import AgentState
from langgraph.nodes import (
    supervisor_node,
    concierge_node,
    service_manager_node,
    consigner_node,
)
from langgraph.edges import router


def create_graph():
    """
    Creates the Raava luxury automotive multi-agent workflow.

    Architecture:
    1. Client inquiry enters via supervisor
    2. Supervisor analyzes and routes to appropriate specialist
    3. Specialist provides expert consultation
    4. Workflow completes

    Agents:
    - Supervisor: Intelligent routing and general inquiries
    - Concierge: Luxury vehicle acquisition and financing
    - Service Manager: Maintenance and service coordination
    - Consigner: Vehicle listing and valuation services
    """

    # Initialize the state graph with our AgentState schema
    workflow = StateGraph(AgentState)

    # Add specialist nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("concierge", concierge_node)
    workflow.add_node("service_manager", service_manager_node)
    workflow.add_node("consigner", consigner_node)

    # Set supervisor as the entry point (first point of contact)
    workflow.set_entry_point("supervisor")

    # Add conditional routing from supervisor to specialists
    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "concierge": "concierge",
            "service_manager": "service_manager",
            "consigner": "consigner",
            "__end__": END,
        },
    )

    # After each specialist completes their consultation, end the workflow
    # (In future versions, we could route back to supervisor for follow-ups)
    workflow.add_edge("concierge", END)
    workflow.add_edge("service_manager", END)
    workflow.add_edge("consigner", END)

    # Compile the graph into an executable workflow
    return workflow.compile()
