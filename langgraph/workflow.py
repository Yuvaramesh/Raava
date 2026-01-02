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
    """Creates the LangGraph multi-agent workflow."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("concierge", concierge_node)
    workflow.add_node("service_manager", service_manager_node)
    workflow.add_node("consigner", consigner_node)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Add conditional edges from supervisor
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

    # After each agent finishes, they return to supervisor or end
    # For simplicity in this flow, they go back to END after answering
    workflow.add_edge("concierge", END)
    workflow.add_edge("service_manager", END)
    workflow.add_edge("consigner", END)

    return workflow.compile()
