"""
Raava Supervisor Agent
Routes user queries to appropriate specialized agents:
- Phase 1: AI Concierge (Vehicle Acquisition)
- Phase 2: AI Service Manager (Maintenance & Service)
- Phase 3: AI Consigner (Vehicle Selling)
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import OPENAI_API_KEY, LLM_MODEL_NAME, LLM_TEMPERATURE


class SupervisorAgent:
    """
    Supervisor Agent - Routes conversations to specialized agents
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=0.3,  # Lower temperature for routing decisions
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava Supervisor Agent - the intelligent router for the Raava Luxury Automotive Platform.

🎯 YOUR ROLE:
You greet customers and route them to the appropriate specialized agent based on their needs.

🤖 AVAILABLE AGENTS:

1. **AI CONCIERGE (Phase 1)** - Vehicle Acquisition
   Routes to: phase1_concierge
   Handles:
   • Buying luxury/sports vehicles
   • Vehicle search and recommendations
   • Finance options and calculations
   • Purchase orders, rentals, bookings
   • Test drives and viewings
   Keywords: buy, purchase, looking for, finance, acquire, rent, book, test drive

2. **AI SERVICE MANAGER (Phase 2)** - Maintenance & Service
   Routes to: phase2_service_manager
   Handles:
   • Scheduled manufacturer services
   • Routine maintenance reminders
   • Non-routine maintenance guidance
   • Service provider recommendations
   • Appointment scheduling
   • Upgrades and enhancements
   Keywords: service, maintenance, repair, check-up, service reminder, upgrade, MOT, inspection

3. **AI CONSIGNER (Phase 3)** - Vehicle Selling
   Routes to: phase3_consigner
   Handles:
   • Selling your vehicle
   • Professional photography
   • Listing descriptions
   • Valuation services
   • Multi-marketplace listings
   • Service history documentation
   Keywords: sell, consign, list, valuation, value my car, selling

📋 ROUTING PROTOCOL:

**INITIAL GREETING (First contact):**
"Welcome to Raava - the luxury automotive platform. I'm your Supervisor Agent.

I can connect you with our specialized teams:

🚗 **Vehicle Acquisition** - Find and purchase your dream car
🔧 **Service Management** - Maintain and upgrade your vehicle  
📸 **Vehicle Consignment** - Sell your car with ease

Which service interests you today?"

**AFTER USER SELECTS:**
Acknowledge and route:
"Perfect! Connecting you to our [SERVICE NAME]..."

Then respond with: "ROUTE_TO: [agent_name]"

**ROUTING CODES:**
• "ROUTE_TO: phase1_concierge" - For buying/acquisition
• "ROUTE_TO: phase2_service_manager" - For service/maintenance
• "ROUTE_TO: phase3_consigner" - For selling/consignment

**IF UNCLEAR:**
Ask clarifying question:
"I'd be happy to help. Are you looking to:
A) Purchase a vehicle
B) Service your vehicle
C) Sell a vehicle"

🎯 RESPONSE RULES:
• Be warm and professional
• Keep responses concise (2-3 sentences)
• Always end with routing decision or clarifying question
• Use "[Replied by: Raava Supervisor Agent]" signature

IMPORTANT: Once you determine the right agent, respond with "ROUTE_TO: [agent_name]" on a new line."""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process user query and route to appropriate agent"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})

        # Check if this is initial contact
        is_first_message = len(messages) <= 1 or not session_context.get("routed")

        # Get last user message
        last_user_message = ""
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break

        # Analyze intent
        routing_decision = self._analyze_routing_intent(
            last_user_message, is_first_message
        )

        # Build conversation
        conversation_messages = [SystemMessage(content=self.system_prompt)]

        # Add recent history
        for msg in messages[-4:]:
            conversation_messages.append(msg)

        # Get supervisor response
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

        # Check if routing decision made
        if "ROUTE_TO:" in response_text:
            # Extract agent name
            route_line = [
                line for line in response_text.split("\n") if "ROUTE_TO:" in line
            ][0]
            agent_name = route_line.split("ROUTE_TO:")[1].strip()

            # Update context
            session_context["routed"] = True
            session_context["active_agent"] = agent_name
            session_context["routing_reason"] = routing_decision["reason"]

            # Clean response (remove routing code from display)
            response_text = response_text.replace(route_line, "").strip()

            return {
                "messages": [AIMessage(content=response_text)],
                "context": session_context,
                "route_to": agent_name,
            }

        return {
            "messages": [response],
            "context": session_context,
            "route_to": None,
        }

    def _analyze_routing_intent(
        self, text: str, is_first_message: bool
    ) -> Dict[str, Any]:
        """Analyze user intent to determine routing"""
        text_lower = text.lower()

        # Keywords for each agent
        acquisition_keywords = [
            "buy",
            "purchase",
            "looking for",
            "find",
            "finance",
            "acquire",
            "rent",
            "rental",
            "book",
            "test drive",
            "viewing",
            "ferrari",
            "porsche",
            "lamborghini",
            "luxury car",
            "sports car",
        ]

        service_keywords = [
            "service",
            "maintenance",
            "repair",
            "check-up",
            "inspection",
            "service reminder",
            "upgrade",
            "enhance",
            "mot",
            "oil change",
            "brake",
            "tire",
            "warranty",
        ]

        consignment_keywords = [
            "sell",
            "consign",
            "list",
            "valuation",
            "value my car",
            "selling",
            "photography",
            "listing",
            "market my car",
        ]

        # Count matches
        acquisition_score = sum(1 for kw in acquisition_keywords if kw in text_lower)
        service_score = sum(1 for kw in service_keywords if kw in text_lower)
        consignment_score = sum(1 for kw in consignment_keywords if kw in text_lower)

        # Determine intent
        if acquisition_score > service_score and acquisition_score > consignment_score:
            return {
                "intent": "acquisition",
                "confidence": "high",
                "agent": "phase1_concierge",
                "reason": "User expressed interest in purchasing/acquiring vehicle",
            }
        elif service_score > acquisition_score and service_score > consignment_score:
            return {
                "intent": "service",
                "confidence": "high",
                "agent": "phase2_service_manager",
                "reason": "User needs vehicle service/maintenance support",
            }
        elif (
            consignment_score > acquisition_score and consignment_score > service_score
        ):
            return {
                "intent": "consignment",
                "confidence": "high",
                "agent": "phase3_consigner",
                "reason": "User wants to sell/consign their vehicle",
            }
        else:
            return {
                "intent": "unclear",
                "confidence": "low",
                "agent": None,
                "reason": "User intent needs clarification",
            }


# Singleton instance
supervisor_agent = SupervisorAgent()
