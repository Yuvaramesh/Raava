from agents.supervisor import get_supervisor_agent
from agents.concierge import ConciergeAgent
from agents.service_manager import ServiceManagerAgent
from agents.consigner import ConsignerAgent
from langchain_core.messages import AIMessage

# Initialize luxury automotive specialists
concierge = ConciergeAgent()
service_manager = ServiceManagerAgent()
consigner = ConsignerAgent()
supervisor_llm, supervisor_prompt = get_supervisor_agent()


async def supervisor_node(state):
    """
    The Raava Supervisor - Intelligent routing for luxury automotive inquiries.

    Analyzes client requests and routes to appropriate specialist:
    - Concierge: Vehicle acquisition, financing, marketplace guidance, BOOKING FLOW
    - Service Manager: Maintenance, repairs, upgrades, service coordination
    - Consigner: Vehicle listings, valuations, market strategy
    """
    messages = state["messages"]

    latest_message = messages[-1].content if messages else ""

    system_context = (
        f"{supervisor_prompt}\n\nLatest client inquiry: {latest_message[:200]}"
    )

    response = await supervisor_llm.ainvoke(
        [{"role": "system", "content": system_context}]
        + [_convert_message(msg) for msg in messages]
    )

    if response.next_agent == "__end__":
        welcome_message = _generate_supervisor_response(latest_message)
        return {
            "messages": [AIMessage(content=welcome_message)],
            "next_agent": "__end__",
            "conversation_phase": "selection",
            "selected_car": "",
            "booking_data": {},
        }

    print(f"🎯 Routing Decision: {response.next_agent}")
    print(f"💭 Reasoning: {response.reasoning}")

    return {
        "next_agent": response.next_agent,
        "conversation_phase": "selection",
        "selected_car": "",
        "booking_data": {},
    }


async def concierge_node(state):
    """
    The Raava AI Concierge - Luxury vehicle acquisition specialist.
    Handles purchases, financing, rentals, and complete booking flow with personal data collection.
    """
    return await concierge.call(state)


async def service_manager_node(state):
    """
    The Raava AI Service Manager - Vehicle care and maintenance specialist.
    Handles servicing, repairs, upgrades, and service provider coordination.
    """
    return await service_manager.call(state)


async def consigner_node(state):
    """
    The Raava AI Consigner - Vehicle listing and valuation specialist.
    Handles listings, photography, market strategy, and seller guidance.
    """
    return await consigner.call(state)


def _convert_message(msg):
    """Convert LangChain message format to dict for API calls"""
    from langchain_core.messages import HumanMessage, AIMessage

    if isinstance(msg, HumanMessage):
        return {"role": "user", "content": msg.content}
    elif isinstance(msg, AIMessage):
        return {"role": "assistant", "content": msg.content}
    return {"role": "user", "content": str(msg)}


def _generate_supervisor_response(query: str) -> str:
    """
    Generate appropriate welcoming response for general inquiries.
    Used when supervisor handles query directly without routing.
    """
    query_lower = query.lower()

    greetings = [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
    ]
    if any(greeting in query_lower for greeting in greetings):
        return """Good day, and welcome to Raava - your personal luxury automotive concierge service.

We specialize in exceptional vehicles from distinguished marques including Ferrari, Lamborghini, Porsche, McLaren, Aston Martin, Bentley, and Rolls-Royce.

Our specialists can assist you with:
• **Vehicle Acquisition** - Finding and financing your perfect luxury or performance vehicle
• **Maintenance Coordination** - Premier service provider connections and care guidance
• **Consignment Services** - Professional listing and market strategy for sellers

How may we serve you today?

[Replied by: Raava Supervisor]"""

    if "raava" in query_lower or "about" in query_lower or "service" in query_lower:
        return """Welcome to Raava - the UK's premier luxury automotive concierge platform.

**Our Mission**: To provide white-glove service for discerning clients seeking exceptional vehicles.

**Our Specialization**: High-end, performance, and luxury automobiles from prestigious marques.

**Our Services**:
1. **AI Concierge** - Personalized vehicle acquisition, financing guidance, and marketplace navigation
2. **AI Service Manager** - Maintenance coordination with vetted premier service providers
3. **AI Consigner** - Professional listing services with strategic market positioning

We don't sell cars. We facilitate automotive dreams.

What brings you to Raava today?

[Replied by: Raava Supervisor]"""

    economy_brands = [
        "kia",
        "hyundai",
        "dacia",
        "basic",
        "cheap",
        "budget",
        "corolla",
        "civic",
        "fiesta",
    ]
    if any(brand in query_lower for brand in economy_brands):
        return """Thank you for your inquiry. Raava specializes exclusively in luxury, performance, and sports vehicles from prestigious marques.

For mainstream and economy vehicles, we'd recommend exploring AutoTrader or CarGurus.

Should you have interest in high-end or performance vehicles in the future, we'd be delighted to assist.

[Replied by: Raava Supervisor]"""

    return """Welcome to Raava. To provide you with the most valuable assistance, could you share a bit more about what you're looking for?

Are you interested in:
• **Acquiring** a luxury or performance vehicle?
• **Maintaining** an existing high-end vehicle?
• **Listing** a vehicle for sale?

This will help me connect you with the perfect specialist for your needs.

[Replied by: Raava Supervisor]"""
