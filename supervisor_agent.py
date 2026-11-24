
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import OPENAI_API_KEY, LLM_MODEL_NAME, LLM_TEMPERATURE


class SupervisorAgent:
    """
    Supervisor Agent - Routes conversations to specialized agents
=======
    Supervisor Agent - Intelligent routing without asking clarifying questions
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=0.3,  # Lower temperature for routing decisions
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava Supervisor Agent - the intelligent router for the Raava Luxury Automotive Platform.

ðŸŽ¯ YOUR ROLE:
You greet customers and route them to the appropriate specialized agent based on their needs.

ðŸ¤– AVAILABLE AGENTS:

1. **AI CONCIERGE (Phase 1)** - Vehicle Acquisition
   Routes to: phase1_concierge
   Handles:
   â€¢ Buying luxury/sports vehicles
   â€¢ Vehicle search and recommendations
   â€¢ Finance options and calculations
   â€¢ Purchase orders, rentals, bookings
   â€¢ Test drives and viewings
   Keywords: buy, purchase, looking for, finance, acquire, rent, book, test drive

2. **AI SERVICE MANAGER (Phase 2)** - Maintenance & Service
   Routes to: phase2_service_manager
   Handles:
   â€¢ Scheduled manufacturer services
   â€¢ Routine maintenance reminders
   â€¢ Non-routine maintenance guidance
   â€¢ Service provider recommendations
   â€¢ Appointment scheduling
   â€¢ Upgrades and enhancements
   Keywords: service, maintenance, repair, check-up, service reminder, upgrade, MOT, inspection

3. **AI CONSIGNER (Phase 3)** - Vehicle Selling
   Routes to: phase3_consigner
   Handles:
   â€¢ Selling your vehicle
   â€¢ Professional photography
   â€¢ Listing descriptions
   â€¢ Valuation services
   â€¢ Multi-marketplace listings
   â€¢ Service history documentation
   Keywords: sell, consign, list, valuation, value my car, selling

ðŸ“‹ ROUTING PROTOCOL:

**INITIAL GREETING (First contact):**
"Welcome to Raava - the luxury automotive platform. I'm your Supervisor Agent.

I can connect you with our specialized teams:

ðŸš— **Vehicle Acquisition** - Find and purchase your dream car
ðŸ”§ **Service Management** - Maintain and upgrade your vehicle  
ðŸ“¸ **Vehicle Consignment** - Sell your car with ease

Which service interests you today?"

**AFTER USER SELECTS:**
Acknowledge and route:
"Perfect! Connecting you to our [SERVICE NAME]..."

Then respond with: "ROUTE_TO: [agent_name]"

**ROUTING CODES:**
â€¢ "ROUTE_TO: phase1_concierge" - For buying/acquisition
â€¢ "ROUTE_TO: phase2_service_manager" - For service/maintenance
â€¢ "ROUTE_TO: phase3_consigner" - For selling/consignment

**IF UNCLEAR:**
Ask clarifying question:
"I'd be happy to help. Are you looking to:
A) Purchase a vehicle
B) Service your vehicle
C) Sell a vehicle"

ðŸŽ¯ RESPONSE RULES:
â€¢ Be warm and professional
â€¢ Keep responses concise (2-3 sentences)
â€¢ Always end with routing decision or clarifying question
â€¢ Use "[Replied by: Raava Supervisor Agent]" signature

IMPORTANT: Once you determine the right agent, respond with "ROUTE_TO: [agent_name]" on a new line."""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process user query and route to appropriate agent"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})

        # Check if this is initial contact
        is_first_message = len(messages) <= 1 or not session_context.get("routed")

=======
            temperature=0.3,
            api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are an intelligent routing system for Raava - a luxury automotive platform.

🎯 YOUR JOB:
Analyze user intent and route IMMEDIATELY to the correct specialist WITHOUT asking clarifying questions.

**ROUTING RULES:**

1. **Vehicle Acquisition (phase1_concierge)** - Route if user mentions:
   - Wanting to buy/purchase a car
   - Looking for a specific vehicle/brand
   - Asking about available cars
   - Interested in financing/payment options
   - Keywords: "buy", "purchase", "looking for", "want", "get", "Lamborghini", "Ferrari", "Porsche", etc.

2. **Service/Maintenance (phase2_service_manager)** - Route if user mentions:
   - Needing service/maintenance/repairs
   - MOT, inspection, check-up
   - Car problems/issues
   - Scheduling service appointment
   - Keywords: "service", "repair", "fix", "maintenance", "MOT", "check", "problem", "issue"

3. **Vehicle Consignment (phase3_consigner)** - Route if user mentions:
   - Wanting to sell their car
   - Consigning a vehicle
   - Getting valuation/appraisal
   - Listing their car for sale
   - Keywords: "sell", "selling", "consign", "list", "valuation", "appraisal"

**RESPONSE FORMAT:**
When you detect intent, respond with a brief friendly acknowledgment followed by:

ROUTE_TO: [agent_name]

**EXAMPLES:**

User: "I want to buy a Lamborghini"
You: "Wonderful! Let me connect you with our vehicle specialist.

ROUTE_TO: phase1_concierge"

User: "buy"
You: "Great! I'll get you to our acquisition expert.

ROUTE_TO: phase1_concierge"

User: "My car needs service"
You: "I'll connect you with our service team right away.

ROUTE_TO: phase2_service_manager"

User: "I want to sell my Ferrari"
You: "Perfect! Our consignment specialist will help you.

ROUTE_TO: phase3_consigner"

User: "Hi" or "Hello"
You: "Hello! What can I help you with today?"
[NO ROUTING - wait for more info]

**CRITICAL:**
- Route IMMEDIATELY when intent is clear
- Don't ask "Are you looking to buy, service, or sell?"
- Only wait for more info if the message is just a greeting with no intent

[Replied by: Raava Routing System]
"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and route based on intent"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})


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
=======
        print(f"\n🎯 SUPERVISOR analyzing: '{last_user_message}'")

        # 🔥 QUICK ROUTING - Bypass LLM for obvious keywords
        quick_route = self._quick_route_check(last_user_message)

        if quick_route:
            print(f"⚡ QUICK ROUTE to {quick_route}")

            # Generate appropriate response
            if quick_route == "phase1_concierge":
                response_text = (
                    "Perfect! Let me connect you with our vehicle specialist."
                )
            elif quick_route == "phase2_service_manager":
                response_text = "I'll connect you with our service team right away."
            else:  # phase3_consigner
                response_text = "Excellent! Our consignment specialist will help you."

            session_context["routed"] = True
            session_context["active_agent"] = quick_route

            return {
                "messages": [AIMessage(content=response_text)],
                "context": session_context,
                "route_to": quick_route,
            }

        # 🔥 Check if it's just a greeting
        if self._is_simple_greeting(last_user_message):
            print("👋 Simple greeting detected - responding without routing")
            return {
                "messages": [
                    AIMessage(content="Hello! What can I help you with today? 😊")
                ],
                "context": session_context,
                "route_to": None,
            }

        # Build conversation for LLM analysis
        conversation_messages = [SystemMessage(content=self.system_prompt)]

        # Add recent messages for context

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
=======
        print(f"🤖 Supervisor response: {response_text[:100]}...")

        # Check if routing decision made
        if "ROUTE_TO:" in response_text:
            # Extract agent name
            route_lines = [
                line for line in response_text.split("\n") if "ROUTE_TO:" in line
            ]
            if route_lines:
                agent_name = route_lines[0].split("ROUTE_TO:")[1].strip()

                print(f"✅ ROUTING to: {agent_name}")

                # Validate agent name
                valid_agents = [
                    "phase1_concierge",
                    "phase2_service_manager",
                    "phase3_consigner",
                ]
                if agent_name not in valid_agents:
                    print(
                        f"⚠️ Invalid agent: {agent_name}, defaulting to phase1_concierge"
                    )
                    agent_name = "phase1_concierge"

                # Update context
                session_context["routed"] = True
                session_context["active_agent"] = agent_name

                # Clean response (remove routing code from display)
                clean_response = response_text.split("ROUTE_TO:")[0].strip()

                return {
                    "messages": [AIMessage(content=clean_response)],
                    "context": session_context,
                    "route_to": agent_name,
                }

        # No routing detected - keep with supervisor
        return {
            "messages": [AIMessage(content=response_text)],
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

=======
    def _quick_route_check(self, text: str) -> str | None:
        """Quick keyword-based routing for obvious cases"""
        text_lower = text.lower()

        # 🔥 BUYING SIGNALS (highest priority - check first)
        buy_keywords = [
            "buy",
            "purchase",
            "looking for",
            "want to buy",
            "get a",
            "interested in",
            "lambo",
            "lamborghini",
            "ferrari",
            "porsche",
            "mclaren",
            "bmw",
            "audi",
            "mercedes",
            "bentley",
            "aston martin",
        ]
        if any(kw in text_lower for kw in buy_keywords):
            return "phase1_concierge"

        # 🔥 SERVICE SIGNALS
        service_keywords = [
            "service",
            "maintenance",
            "repair
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
=======
            "mot",
            "check",
            "fix",
            "servicing",
            "inspection",
            "problem",
            "issue",
        ]
        if any(kw in text_lower for kw in service_keywords):
            return "phase2_service_manager"

        # 🔥 SELLING SIGNALS
        sell_keywords = [
            "sell",
            "selling",
            "consign",
            "consignment",
            "list my",
            "valuation",
            "appraisal",
        ]
        if any(kw in text_lower for kw in sell_keywords):
            return "phase3_consigner"

        return None

    def _is_simple_greeting(self, text: str) -> bool:
        """Check if message is just a greeting"""
        text_lower = text.lower().strip()
        greetings = [
            "hi",
            "hello",
            "hey",
            "greetings",
            "good morning",
            "good afternoon",
            "good evening",
        ]
        # Only return True if it's JUST a greeting (not "hi I want to buy")
        return text_lower in greetings or len(text_lower) <= 3



# Singleton instance
supervisor_agent = SupervisorAgent()
