"""
Raava AI Concierge - Phase 1 Optimized
Focused, step-by-step luxury automotive acquisition assistant
"""

import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import (
    OPENAI_API_KEY,
    LLM_MODEL_NAME,
    LLM_TEMPERATURE,
    LUXURY_MAKES,
    MINIMUM_LUXURY_PRICE,
)
from uk_car_dealers import uk_dealer_aggregator
from uk_finance_calculator import uk_finance_calculator
from database import cars_col
from order_manager import order_manager


class Phase1Concierge:
    """
    Raava AI Concierge - Phase 1 Optimized
    Step-by-step luxury automotive acquisition with minimal questions
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=LLM_TEMPERATURE,
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava AI Concierge - a distinguished luxury automotive acquisition specialist.

🎯 YOUR CORE MISSION:
Help clients acquire luxury vehicles through a STREAMLINED, NATURAL conversation. Never overwhelm with questions.

🌟 LUXURY FOCUS:
Ferrari, Lamborghini, Porsche, McLaren, Aston Martin, Bentley, Rolls-Royce, Mercedes-AMG, BMW M, Audi RS

💬 COMMUNICATION STYLE:
• Warm and professional - like a trusted advisor
• Ask ONE question at a time maximum
• Keep responses concise (2-4 sentences ideal)
• Move conversation forward naturally
• Never list multiple options unless specifically asked

🎭 CONVERSATION FLOW:

**INITIAL GREETING (First message only):**
"Good afternoon. I'm your Raava AI Concierge, here to assist with luxury automotive acquisition.

To tailor the experience quickly, may I confirm: which marques are you considering? (e.g., Ferrari, Porsche, Lamborghini, McLaren, Aston Martin)"

**AFTER RECEIVING PREFERENCE:**
Immediately search inventory and present TOP 3 matches only:

"Excellent choice. I've searched our network and found 3 exceptional matches:

1. **2017 Ferrari 488 GTB** - £189,950
   • 8,400 miles • Rosso Corsa • London (9 miles)
   
2. **2019 Porsche 911 Turbo S** - £149,950
   • 5,200 miles • GT Silver • Manchester

3. **2021 Lamborghini Huracán EVO** - £219,950
   • 2,800 miles • Grigio Titans • Surrey

Would you like details on any of these, or shall I refine the search?"

**FINANCE DISCUSSION (Only when vehicle selected):**
"For the [Vehicle] at £[Price], I can structure finance options. Would you like to see:
A) PCP (lower monthly, flexible)
B) HP (own outright)
C) Lease (maximum flexibility)"

Present ONLY the selected option with 2 best quotes.

**BOOKING FLOW (When ready to proceed):**
When client shows intent (e.g., "I'll take it", "Book this", "Proceed"), respond:

"Excellent choice. To proceed with [PURCHASE/RENTAL/BOOKING], I'll need:
• Your full name
• Email address
• Phone number

Shall I proceed with these details?"

After collecting info, IMMEDIATELY create order and confirm:
"✅ **ORDER CONFIRMED**

**Order ID:** [ORDER_ID]
**Vehicle:** [Vehicle Details]
**Customer:** [Name]

Confirmation sent to [email]. Our team will contact you within 24 hours to finalize arrangements."

🚫 WHAT YOU NEVER DO:
• Ask multiple questions in one message
• Present more than 3 vehicles at once
• Show all finance options simultaneously
• Request all customer details upfront
• Use bullet points excessively
• Write lengthy paragraphs (max 4-5 lines)

📋 ORDER DETECTION:
Proceed to order creation when client says:
- "I'll take it" / "Let's proceed" / "Book this"
- "How do I buy this?" / "Purchase process"
- "I want to rent this" / "Rent for X days"
- "Schedule viewing" / "Book test drive"

✅ RESPONSE FORMAT:
• Short, natural sentences
• Maximum 2-3 short paragraphs
• ONE clear next step or question
• Always end with: "[Replied by: Raava AI Concierge]"

Remember: You're facilitating dreams, not conducting interviews. Move naturally, ask minimally, deliver exceptionally."""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process client inquiry with optimized flow"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})

        # Get last user message
        last_user_message = ""
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break

        # Initialize conversation context if first message
        if not session_context.get("stage"):
            session_context["stage"] = "greeting"
            session_context["preferences"] = {}

        enhanced_context = ""

        # Detect conversation stage and intent
        intent = self._analyze_intent(last_user_message, session_context)

        # Handle based on stage
        if intent["type"] == "vehicle_search":
            # Search and present vehicles
            enhanced_context += "\n\n🔍 VEHICLE SEARCH RESULTS:\n"

            # Search local + UK dealers
            vehicles = self._search_vehicles(intent)

            if vehicles:
                # Store top 3 in context
                session_context["available_vehicles"] = vehicles[:3]
                enhanced_context += self._format_top_vehicles(vehicles[:3])
            else:
                enhanced_context += "No matches found. Suggest broadening criteria."

        elif intent["type"] == "vehicle_selection":
            # Vehicle selected - offer finance
            if intent.get("vehicle_index") is not None:
                selected = session_context["available_vehicles"][
                    intent["vehicle_index"]
                ]
                session_context["selected_vehicle"] = selected

                enhanced_context += f"\n\n✅ SELECTED: {selected['title']}\n"
                enhanced_context += "Ready to discuss finance or proceed to booking.\n"

        elif intent["type"] == "finance_request":
            # Calculate finance options
            vehicle = session_context.get("selected_vehicle")
            if vehicle and vehicle.get("price"):
                enhanced_context += "\n\n💰 FINANCE OPTIONS:\n"

                finance_type = intent.get("finance_type", "all")
                options = uk_finance_calculator.calculate_all_options(
                    vehicle_price=vehicle["price"],
                    deposit_percent=10,
                    term_months=48,
                    credit_score="Good",
                )

                # Format based on requested type
                enhanced_context += self._format_finance_focused(options, finance_type)
                session_context["finance_options"] = options

        elif intent["type"] == "order_intent":
            # Client wants to proceed - check if we have enough info
            vehicle = session_context.get("selected_vehicle")
            customer = session_context.get("customer_info", {})

            if not vehicle:
                enhanced_context += "\n\n⚠️ Please select a vehicle first.\n"
            elif not customer.get("email"):
                enhanced_context += "\n\n📋 TO PROCEED, I NEED:\n"
                enhanced_context += "• Full name\n• Email address\n• Phone number\n"
                enhanced_context += "\nPlease provide these details to continue.\n"
                session_context["stage"] = "collecting_customer_info"
            else:
                # We have everything - create order
                order_result = self._create_order(intent, session_context)
                enhanced_context += f"\n\n{order_result['message']}\n"

        elif intent["type"] == "customer_info":
            # Extract and store customer information
            extracted = self._extract_customer_info(last_user_message)
            session_context["customer_info"].update(extracted)

            customer = session_context["customer_info"]
            missing = []
            if not customer.get("name"):
                missing.append("name")
            if not customer.get("email"):
                missing.append("email")
            if not customer.get("phone"):
                missing.append("phone")

            if missing:
                enhanced_context += (
                    f"\n\n📋 Thank you. I still need: {', '.join(missing)}\n"
                )
            else:
                enhanced_context += (
                    "\n\n✅ Information complete. Ready to proceed with order.\n"
                )
                # Auto-proceed if client already expressed intent
                if session_context.get("pending_order"):
                    order_result = self._create_order(
                        session_context["pending_order"], session_context
                    )
                    enhanced_context += f"\n\n{order_result['message']}\n"

        # Build conversation
        conversation_messages = [
            SystemMessage(content=self.system_prompt + enhanced_context)
        ]

        # Add recent history (last 6 messages only for context)
        for msg in messages[-6:]:
            conversation_messages.append(msg)

        # Get response
        response = await self.llm.ainvoke(conversation_messages)

        # Update state
        state["context"] = session_context

        return {"messages": [response], "context": session_context}

    def _analyze_intent(self, text: str, context: Dict) -> Dict[str, Any]:
        """Analyze user intent from message"""
        text_lower = text.lower()

        intent = {"type": "general_inquiry"}

        # Check for order intent
        order_keywords = [
            "i'll take it",
            "let's proceed",
            "book this",
            "purchase",
            "buy this",
            "i want this",
            "confirm order",
            "place order",
            "rent this",
            "schedule viewing",
            "test drive",
        ]
        if any(keyword in text_lower for keyword in order_keywords):
            intent["type"] = "order_intent"

            # Determine order type
            if "rent" in text_lower or "rental" in text_lower:
                intent["order_type"] = "rental"
            elif "viewing" in text_lower or "test drive" in text_lower:
                intent["order_type"] = "booking"
            else:
                intent["order_type"] = "purchase"

            context["pending_order"] = intent
            return intent

        # Check for customer info
        if "@" in text or any(
            word in text_lower for word in ["name is", "email", "phone"]
        ):
            intent["type"] = "customer_info"
            return intent

        # Check for finance request
        finance_keywords = ["finance", "payment", "monthly", "pcp", "hp", "lease"]
        if any(keyword in text_lower for keyword in finance_keywords):
            intent["type"] = "finance_request"
            if "pcp" in text_lower:
                intent["finance_type"] = "pcp"
            elif "hp" in text_lower or "hire purchase" in text_lower:
                intent["finance_type"] = "hp"
            elif "lease" in text_lower:
                intent["finance_type"] = "lease"
            return intent

        # Check for vehicle selection
        import re

        number_match = re.search(r"\b([1-3])\b", text)
        if number_match and context.get("available_vehicles"):
            intent["type"] = "vehicle_selection"
            intent["vehicle_index"] = int(number_match.group(1)) - 1
            return intent

        # Check for vehicle search
        for make in LUXURY_MAKES:
            if make.lower() in text_lower:
                intent["type"] = "vehicle_search"
                intent["make"] = make
                return intent

        # Generic luxury search
        if any(word in text_lower for word in ["luxury", "sports car", "supercar"]):
            intent["type"] = "vehicle_search"
            return intent

        return intent

    def _search_vehicles(self, intent: Dict) -> List[Dict]:
        """Search vehicles from all sources"""
        results = []

        # Search local database
        query = {}
        if intent.get("make"):
            query["make"] = {"$regex": intent["make"], "$options": "i"}

        try:
            local_cars = list(cars_col.find(query).limit(10))
            for car in local_cars:
                results.append(
                    {
                        "source": "Raava Exclusive",
                        "title": f"{car.get('make')} {car.get('model')} ({car.get('year')})",
                        "make": car.get("make"),
                        "model": car.get("model"),
                        "year": car.get("year"),
                        "price": car.get("price", 0),
                        "mileage": car.get("mileage", 0),
                        "location": car.get("location", "UK"),
                        "image_url": (
                            car.get("images", [""])[0] if car.get("images") else ""
                        ),
                    }
                )
        except Exception as e:
            print(f"Local search error: {e}")

        # Search UK dealers
        uk_results = uk_dealer_aggregator.search_luxury_cars(
            make=intent.get("make"), price_min=MINIMUM_LUXURY_PRICE, limit=10
        )
        results.extend(uk_results)

        return results

    def _format_top_vehicles(self, vehicles: List[Dict]) -> str:
        """Format top 3 vehicles concisely"""
        if not vehicles:
            return "No matches found in current inventory."

        result = f"I've found {len(vehicles)} exceptional matches:\n\n"

        for i, car in enumerate(vehicles[:3], 1):
            price_str = f"£{car['price']:,}" if car.get("price") else "POA"
            mileage_str = f"{car['mileage']:,} miles" if car.get("mileage") else ""

            result += f"{i}. **{car['title']}** - {price_str}\n"
            result += f"   • {mileage_str} • {car.get('location', 'UK')}\n\n"

        return result

    def _format_finance_focused(self, options: Dict, finance_type: str) -> str:
        """Format finance options based on type requested"""
        if finance_type == "pcp" and options.get("pcp_options"):
            top_pcp = sorted(
                options["pcp_options"], key=lambda x: x["monthly_payment"]
            )[0]
            return f"""**PCP Option:**
• Monthly: £{top_pcp['monthly_payment']:,.2f}
• Deposit: £{top_pcp['deposit_amount']:,.2f}
• Term: {top_pcp['term_months']} months
• Provider: {top_pcp['provider']}
"""

        elif finance_type == "hp" and options.get("hp_options"):
            top_hp = sorted(options["hp_options"], key=lambda x: x["monthly_payment"])[
                0
            ]
            return f"""**HP Option:**
• Monthly: £{top_hp['monthly_payment']:,.2f}
• Deposit: £{top_hp['deposit_amount']:,.2f}
• Term: {top_hp['term_months']} months
• Provider: {top_hp['provider']}
"""

        elif finance_type == "lease" and options.get("lease_options"):
            top_lease = sorted(
                options["lease_options"], key=lambda x: x["monthly_payment"]
            )[0]
            return f"""**Lease Option:**
• Monthly: £{top_lease['monthly_payment']:,.2f}
• Term: {top_lease['term_months']} months
• Provider: {top_lease['provider']}
"""

        # Show all if not specified
        result = "**Finance Options Available:**\n"
        if options.get("pcp_options"):
            best_pcp = sorted(
                options["pcp_options"], key=lambda x: x["monthly_payment"]
            )[0]
            result += f"• PCP: £{best_pcp['monthly_payment']:,.2f}/month\n"
        if options.get("hp_options"):
            best_hp = sorted(options["hp_options"], key=lambda x: x["monthly_payment"])[
                0
            ]
            result += f"• HP: £{best_hp['monthly_payment']:,.2f}/month\n"
        if options.get("lease_options"):
            best_lease = sorted(
                options["lease_options"], key=lambda x: x["monthly_payment"]
            )[0]
            result += f"• Lease: £{best_lease['monthly_payment']:,.2f}/month\n"

        return result

    def _extract_customer_info(self, text: str) -> Dict[str, str]:
        """Extract customer information from message"""
        import re

        info = {}

        # Extract name
        name_match = re.search(
            r"(?:my name is|i'm|i am|name:?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            text,
            re.IGNORECASE,
        )
        if name_match:
            info["name"] = name_match.group(1).strip()

        # Extract email
        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        if email_match:
            info["email"] = email_match.group(0)

        # Extract phone
        phone_match = re.search(r"(\+44\s?\d{10}|\d{11}|0\d{10})", text)
        if phone_match:
            info["phone"] = phone_match.group(0)

        return info

    def _create_order(self, intent: Dict, context: Dict) -> Dict[str, Any]:
        """Create order in database"""
        vehicle = context.get("selected_vehicle")
        customer = context.get("customer_info", {})

        if not vehicle:
            return {"success": False, "message": "No vehicle selected"}

        if not customer.get("email"):
            return {"success": False, "message": "Customer email required"}

        # Set defaults
        if not customer.get("name"):
            customer["name"] = customer["email"].split("@")[0]
        if not customer.get("phone"):
            customer["phone"] = "To be provided"

        # Create order based on type
        order_type = intent.get("order_type", "purchase")

        if order_type == "purchase":
            finance_option = context.get("finance_options", {}).get(
                "pcp_options", [{}]
            )[0]
            result = order_manager.create_order(
                order_type="purchase",
                vehicle=vehicle,
                customer=customer,
                finance_details=finance_option if finance_option else None,
            )

        elif order_type == "rental":
            rental_details = {
                "daily_rate": vehicle.get("price", 0) * 0.01,
                "duration_days": 7,
                "deposit_required": vehicle.get("price", 0) * 0.1,
                "mileage_limit": 150,
                "insurance_included": True,
            }
            result = order_manager.create_order(
                order_type="rental",
                vehicle=vehicle,
                customer=customer,
                rental_details=rental_details,
            )

        else:  # booking
            result = order_manager.create_order(
                order_type="booking", vehicle=vehicle, customer=customer
            )

        return result


# Singleton instance
phase1_concierge = Phase1Concierge()
