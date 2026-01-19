"""
Raava AI Concierge - Phase 1 FULLY FIXED
Properly searches vehicles, detects selections, handles payment, and creates orders
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
)
from database import cars_col, orders_col
from order_manager import order_manager
from uk_finance_calculator import uk_finance_calculator
from datetime import datetime
import re


class Phase1Concierge:
    """
    Raava AI Concierge - FULLY FIXED with proper flow
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=LLM_TEMPERATURE,
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are a luxury car specialist at Raava. Speak like a knowledgeable friend.

🎯 CONVERSATION FLOW:

**Stage 1 - After Routing:**
Ask about the make/model they're interested in.

**Stage 2 - After Make/Model Mentioned:**
The system will search and show vehicles. Ask them to pick one (1, 2, or 3).

**Stage 3 - After Vehicle Selected:**
Ask about payment: "Cash payment or financing?"

**Stage 4 - If Finance:**
Ask which type: "PCP, HP, or Lease?"

**Stage 5 - Collect Details:**
Ask for: Name, Email, Phone (one at a time)

**Stage 6 - Confirm:**
Review everything and create the order.

🎯 RULES:
- ONE question at a time
- Be warm and conversational
- No bullet points in responses
- Natural flow

[Replied by: Raava AI Concierge]
"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process with FIXED flow"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})

        # Get last user message
        last_user_message = ""
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break

        # 🔥 Initialize if needed
        if (
            not session_context.get("stage")
            or session_context.get("stage") == "supervisor_greeting"
        ):
            session_context["stage"] = "greeting"
            session_context["preferences"] = {}
            session_context["customer_info"] = {}

        print(f"\n🔍 CONCIERGE - Stage: {session_context.get('stage')}")
        print(f"📝 User: {last_user_message}")
        print(f"🚗 Has Vehicle: {bool(session_context.get('selected_vehicle'))}")
        print(f"💳 Payment: {session_context.get('payment_method')}")
        print(
            f"👤 Customer Email: {session_context.get('customer_info', {}).get('email')}"
        )

        enhanced_context = ""

        # 🔥 STEP 1: Check if ready to create order
        if self._should_create_order(session_context):
            print("🔥 CREATING ORDER NOW!")
            order_result = self._create_order_now(session_context)

            if order_result.get("success"):
                print(f"✅ ORDER CREATED: {order_result.get('order_id')}")
                return {
                    "messages": [AIMessage(content=order_result["message"])],
                    "context": session_context,
                }
            else:
                enhanced_context += f"\n\n❌ ERROR: {order_result.get('message')}\n"

        # 🔥 STEP 2: Detect intent and process
        text_lower = last_user_message.lower()

        # Check for vehicle make (Lamborghini, Ferrari, etc.)
        vehicle_make = None
        for make in LUXURY_MAKES:
            if make.lower() in text_lower:
                vehicle_make = make
                break

        # 🔥 VEHICLE SEARCH
        if vehicle_make and not session_context.get("available_vehicles"):
            print(f"🔍 Searching for {vehicle_make}...")
            vehicles = self._search_vehicles(vehicle_make)

            if vehicles:
                session_context["available_vehicles"] = vehicles[:3]
                session_context["stage"] = "vehicle_selection"

                enhanced_context += "\n\n🚗 VEHICLES FOUND:\n"
                enhanced_context += self._format_vehicles(vehicles[:3])
                enhanced_context += (
                    "\nASK: Which one would you like? (Pick 1, 2, or 3)\n"
                )

                print(f"✅ Found {len(vehicles)} vehicles, showing top 3")
            else:
                enhanced_context += (
                    f"\n\n❌ No {vehicle_make} vehicles found in inventory.\n"
                )

        # 🔥 VEHICLE SELECTION (detect "1", "2", "3" or "I will proceed with 1")
        elif session_context.get(
            "stage"
        ) == "vehicle_selection" and session_context.get("available_vehicles"):
            # Look for selection patterns
            selection_match = re.search(
                r"(?:pick|choose|select|take|proceed with|want)\s*([1-3])", text_lower
            )
            if not selection_match:
                # Check for standalone number
                selection_match = re.search(r"^([1-3])$", text_lower.strip())

            if selection_match:
                idx = int(selection_match.group(1)) - 1
                vehicles = session_context["available_vehicles"]

                if 0 <= idx < len(vehicles):
                    selected = vehicles[idx]
                    session_context["selected_vehicle"] = selected
                    session_context["stage"] = "payment_method_selection"

                    enhanced_context += (
                        f"\n\n✅ VEHICLE SELECTED: {selected['title']}\n"
                    )
                    enhanced_context += f"Price: £{selected.get('price', 0):,}\n"
                    enhanced_context += "ASK: Cash payment or financing?\n"

                    print(f"✅ Selected vehicle: {selected['title']}")

        # 🔥 PAYMENT METHOD SELECTION
        elif session_context.get("stage") == "payment_method_selection":
            if any(
                w in text_lower
                for w in [
                    "cash",
                    "pay cash",
                    "outright",
                    "full payment",
                    "cash on delivery",
                ]
            ):
                session_context["payment_method"] = "cash"
                session_context["stage"] = "collecting_customer_info"
                enhanced_context += "\n\n✅ CASH PAYMENT SELECTED\n"
                enhanced_context += "ASK: Your full name?\n"
                print("✅ Payment: CASH")

            elif any(
                w in text_lower for w in ["finance", "financing", "monthly", "loan"]
            ):
                session_context["payment_method"] = "finance"
                session_context["stage"] = "finance_type_selection"
                enhanced_context += "\n\n✅ FINANCE SELECTED\n"
                enhanced_context += "ASK: PCP, HP, or Lease?\n"
                print("✅ Payment: FINANCE")

        # 🔥 FINANCE TYPE SELECTION
        elif session_context.get("stage") == "finance_type_selection":
            if "pcp" in text_lower:
                finance_type = "pcp"
            elif "hp" in text_lower or "hire" in text_lower:
                finance_type = "hp"
            elif "lease" in text_lower:
                finance_type = "lease"
            else:
                finance_type = None

            if finance_type:
                session_context["finance_type"] = finance_type
                session_context["stage"] = "collecting_customer_info"

                # Calculate finance
                vehicle = session_context.get("selected_vehicle")
                if vehicle:
                    options = uk_finance_calculator.calculate_all_options(
                        vehicle_price=vehicle["price"],
                        deposit_percent=10,
                        term_months=48,
                        credit_score="Good",
                    )
                    session_context["finance_options"] = options

                    enhanced_context += f"\n\n💰 {finance_type.upper()} CALCULATED\n"
                    enhanced_context += self._format_finance(options, finance_type)

                enhanced_context += "\nASK: Your full name?\n"
                print(f"✅ Finance type: {finance_type}")

        # 🔥 CUSTOMER INFO COLLECTION
        elif session_context.get("stage") == "collecting_customer_info":
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
                enhanced_context += f"\n\n📋 Still need: {', '.join(missing)}\n"
                if not customer.get("name"):
                    enhanced_context += "ASK: Your full name?\n"
                elif not customer.get("email"):
                    enhanced_context += "ASK: Your email address?\n"
                elif not customer.get("phone"):
                    enhanced_context += "ASK: Your mobile number?\n"
            else:
                session_context["stage"] = "ready_to_order"
                enhanced_context += (
                    "\n\n✅ ALL INFO COLLECTED - READY TO CREATE ORDER\n"
                )
                enhanced_context += "SAY: Great! Let me confirm your order...\n"
                print("✅ All customer info collected!")

        # Build LLM conversation
        conversation_messages = [
            SystemMessage(content=self.system_prompt + enhanced_context)
        ]

        # Add recent messages
        for msg in messages[-6:]:
            conversation_messages.append(msg)

        # Get response
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

        # Update state
        state["context"] = session_context

        print(f"✅ Returning - Stage: {session_context.get('stage')}")

        return {
            "messages": [AIMessage(content=response_text)],
            "context": session_context,
        }

    def _should_create_order(self, context: Dict) -> bool:
        """Check if ready to create order"""
        vehicle = context.get("selected_vehicle")
        payment = context.get("payment_method")
        customer = context.get("customer_info", {})

        if not vehicle:
            return False
        if not payment:
            return False
        if payment == "finance" and not context.get("finance_type"):
            return False
        if not customer.get("email") or not customer.get("name"):
            return False
        if context.get("stage") != "ready_to_order":
            return False

        return True

    def _create_order_now(self, context: Dict) -> Dict[str, Any]:
        """CREATE ORDER IN DATABASE"""
        try:
            vehicle = context.get("selected_vehicle")
            customer = context.get("customer_info")
            payment_method = context.get("payment_method")
            finance_type = context.get("finance_type")

            print(f"\n🔥 CREATING ORDER:")
            print(f"   Vehicle: {vehicle.get('title')}")
            print(f"   Payment: {payment_method}")
            print(f"   Customer: {customer.get('email')}")

            # Prepare finance details
            finance_details = None
            if payment_method == "finance" and finance_type:
                options = context.get("finance_options", {})
                key = f"{finance_type}_options"
                if options.get(key):
                    finance_details = options[key][0]

            # CREATE ORDER
            result = order_manager.create_order(
                order_type="purchase",
                vehicle=vehicle,
                customer=customer,
                finance_details=finance_details,
            )

            if result.get("success"):
                order_id = result.get("order_id")
                print(f"✅ ORDER CREATED: {order_id}")

                # Mark order created
                context["order_created"] = True
                context["order_id"] = order_id
                context["stage"] = "order_completed"

                return result
            else:
                return result

        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"Error: {str(e)}"}

    def _search_vehicles(self, make: str) -> List[Dict]:
        """Search vehicles by make"""
        try:
            query = {"make": {"$regex": make, "$options": "i"}}
            cars = list(cars_col.find(query).limit(10))

            results = []
            for car in cars:
                vehicle = {
                    "source": "Raava Exclusive",
                    "title": f"{car.get('make')} {car.get('model')} ({car.get('year')})",
                    "make": car.get("make"),
                    "model": car.get("model"),
                    "year": car.get("year"),
                    "price": car.get("price", 0),
                    "mileage": car.get("mileage", 0),
                    "fuel_type": car.get("fuel_type", "Petrol"),
                    "body_type": car.get("body_type", "Coupe"),
                    "location": car.get("location", "UK"),
                }
                results.append(vehicle)

            return results
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

    def _format_vehicles(self, vehicles: List[Dict]) -> str:
        """Format vehicles for display"""
        result = ""
        for i, car in enumerate(vehicles, 1):
            result += f"{i}. {car['title']} - £{car['price']:,}\n"
            result += f"   • {car['mileage']:,} miles • {car['location']}\n\n"
        return result

    def _format_finance(self, options: Dict, finance_type: str) -> str:
        """Format finance options"""
        key = f"{finance_type}_options"
        if options.get(key):
            opt = options[key][0]
            return f"Monthly: £{opt['monthly_payment']:,.2f} | Provider: {opt['provider']}\n"
        return ""

    def _extract_customer_info(self, text: str) -> Dict[str, str]:
        """Extract customer info from text"""
        info = {}

        # Email
        email = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        if email:
            info["email"] = email.group(0)
            print(f"   📧 Email: {info['email']}")

        # Phone
        phone = re.search(r"(\+?\d{10,15})", text)
        if phone:
            info["phone"] = phone.group(0)
            print(f"   📞 Phone: {info['phone']}")

        # Name - extract words, skip common words
        text_clean = text
        if email:
            text_clean = text_clean.replace(email.group(0), "")
        if phone:
            text_clean = text_clean.replace(phone.group(0), "")

        parts = text_clean.replace(",", " ").split()
        name_candidates = []

        for word in parts:
            if "@" in word or word.isdigit() or "+" in word:
                continue
            if word.lower() in ["my", "name", "is", "email", "phone", "and", "the"]:
                continue
            if len(word) > 1 and word.replace(".", "").isalpha():
                name_candidates.append(word.strip())

        if name_candidates:
            name = " ".join(name_candidates[:2])
            info["name"] = " ".join(word.capitalize() for word in name.split())
            print(f"   👤 Name: {info['name']}")

        return info


# Singleton
phase1_concierge = Phase1Concierge()
