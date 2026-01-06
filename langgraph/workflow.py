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
    Creates the Raava luxury automotive multi-agent workflow with booking flow support.

    Architecture:
    1. Client inquiry enters via supervisor
    2. Supervisor analyzes and routes to appropriate specialist
    3. Specialist provides expert consultation and processes bookings
    4. Workflow completes with order confirmation in MongoDB

    Agents:
    - Supervisor: Intelligent routing and general inquiries
    - Concierge: Luxury vehicle acquisition, financing, and booking flow
    - Service Manager: Maintenance and service coordination
    - Consigner: Vehicle listing and valuation services
    """

    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("concierge", concierge_node)
    workflow.add_node("service_manager", service_manager_node)
    workflow.add_node("consigner", consigner_node)

    workflow.set_entry_point("supervisor")

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

    workflow.add_edge("concierge", END)
    workflow.add_edge("service_manager", END)
    workflow.add_edge("consigner", END)

    return workflow.compile()
