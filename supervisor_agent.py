"""
Raava Supervisor Agent - FIXED ROUTING
Routes user queries to appropriate specialized agents
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
            temperature=0.3,
            api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are a warm, welcoming concierge at Raava - a luxury automotive platform.

🎯 YOUR JOB:
1. Greet new visitors warmly
2. Listen to what they need
3. Route them to the right specialist IMMEDIATELY

**For First-Time Visitors:**
"Welcome to Raava! I'm here to help. Are you looking to buy a car, service your vehicle, or sell one?"

**When They Express a Need:**
Analyze their intent and route IMMEDIATELY:

- Buying/Looking for a car → Route to phase1_concierge
- Service/Maintenance/Repair → Route to phase2_service_manager  
- Selling/Consigning a car → Route to phase3_consigner

**ROUTING FORMAT:**
When you detect clear intent, respond with:
"[Brief acknowledgment]

ROUTE_TO: [agent_name]"

**CRITICAL:**
- Route IMMEDIATELY when intent is clear
- Don't ask clarifying questions if intent is obvious
- Don't explain what each specialist does - just route
- Be warm but brief

**Examples:**

User: "I want to buy my dream car"
You: "Wonderful! Let me connect you with our acquisition specialist.

ROUTE_TO: phase1_concierge"

User: "I want to buy latest model lambo"
You: "Perfect! Connecting you to our luxury vehicle specialist now.

ROUTE_TO: phase1_concierge"

User: "buy"
You: "Great! Let me get you to our vehicle specialist.

ROUTE_TO: phase1_concierge"

User: "I need service for my car"
You: "Of course! Connecting you with our service expert.

ROUTE_TO: phase2_service_manager"

User: "I want to sell my Ferrari"
You: "Excellent! Our consignment specialist will help you.

ROUTE_TO: phase3_consigner"

[Replied by: Raava Supervisor]
"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process user query and route to appropriate agent"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})

        # Get last user message
        last_user_message = ""
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break

        print(f"\n🎯 SUPERVISOR analyzing: '{last_user_message}'")

        # Quick routing check using keywords (bypass LLM for obvious cases)
        quick_route = self._quick_route_check(last_user_message)

        if quick_route:
            print(f"⚡ QUICK ROUTE to {quick_route}")

            # Generate appropriate response
            if quick_route == "phase1_concierge":
                response_text = "Perfect! Let me connect you with our vehicle acquisition specialist."
            elif quick_route == "phase2_service_manager":
                response_text = "Of course! Connecting you with our service expert."
            else:  # phase3_consigner
                response_text = "Excellent! Our consignment specialist will help you."

            session_context["routed"] = True
            session_context["active_agent"] = quick_route

            return {
                "messages": [AIMessage(content=response_text)],
                "context": session_context,
                "route_to": quick_route,
            }

        # Build conversation for LLM
        conversation_messages = [SystemMessage(content=self.system_prompt)]

        # Add recent history (last 2 exchanges)
        for msg in messages[-4:]:
            conversation_messages.append(msg)

        # Get supervisor response
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

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

    def _quick_route_check(self, text: str) -> str | None:
        """Quick keyword-based routing for obvious cases"""
        text_lower = text.lower()

        # Strong buy signals
        buy_keywords = [
            "buy",
            "purchase",
            "looking for",
            "want to buy",
            "lambo",
            "ferrari",
            "porsche",
        ]
        if any(kw in text_lower for kw in buy_keywords):
            return "phase1_concierge"

        # Strong service signals
        service_keywords = ["service", "maintenance", "repair", "mot", "check", "fix"]
        if any(kw in text_lower for kw in service_keywords):
            return "phase2_service_manager"

        # Strong sell signals
        sell_keywords = ["sell", "consign", "list my", "selling"]
        if any(kw in text_lower for kw in sell_keywords):
            return "phase3_consigner"

        return None


# Singleton instance
supervisor_agent = SupervisorAgent()
