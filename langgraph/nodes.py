from agents.supervisor import get_supervisor_agent
from agents.concierge import ConciergeAgent
from agents.service_manager import ServiceManagerAgent
from agents.consigner import ConsignerAgent

# Initialize agents
concierge = ConciergeAgent()
service_manager = ServiceManagerAgent()
consigner = ConsignerAgent()
supervisor_llm, supervisor_prompt = get_supervisor_agent()


async def supervisor_node(state):
    """The supervisor node that decides which agent to call next."""
    messages = state["messages"]
    response = await supervisor_llm.ainvoke(
        [{"role": "system", "content": supervisor_prompt}] + messages
    )
    return {"next_agent": response.next_agent}


async def concierge_node(state):
    """The concierge agent node."""
    return await concierge.call(state)


async def service_manager_node(state):
    """The service manager agent node."""
    return await service_manager.call(state)


async def consigner_node(state):
    """The consigner agent node."""
    return await consigner.call(state)
