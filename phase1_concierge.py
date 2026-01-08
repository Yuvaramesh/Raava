"""
Raava AI Concierge - Phase 1 FIXED
PROPERLY creates orders and stores in Orders collection
FIXED: Intent detection to prevent misreading customer info as vehicle selection
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
from database import cars_col, orders_col
from order_manager import order_manager
from datetime import datetime
import re


class Phase1Concierge:
    """
    Raava AI Concierge - FIXED ORDER CREATION
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=LLM_TEMPERATURE,
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava AI Concierge - luxury automotive acquisition specialist.

🎯 MISSION: Help clients acquire vehicles with PROPER ORDER CREATION

💬 CONVERSATION FLOW:

1. **GREETING**: Ask which luxury marque they're considering
2. **VEHICLE SEARCH**: Show TOP 3 matches
3. **VEHICLE SELECTION**: When they pick one, ask payment method
4. **PAYMENT METHOD**: "Cash or Finance?"
5. **FINANCE TYPE** (if finance): "PCP, HP, or Lease?"
6. **CUSTOMER DETAILS**: Get name, email, phone
7. **CREATE ORDER**: Immediately create and confirm

🔑 CRITICAL ORDER CREATION RULES:

When you have ALL of these:
✅ Vehicle selected
✅ Payment method chosen (cash OR finance type selected)
✅ Customer details (name, email, phone)

Then you MUST respond with EXACTLY this format:

"CREATE_ORDER_NOW

Vehicle: [vehicle details]
Payment: [cash/finance type]
Customer: [name, email, phone]"

This triggers the order creation system.

PAYMENT METHOD QUESTIONS:
- For purchases: "Would you prefer Cash Payment or Finance Options?"
- For finance: "Which finance type: PCP, HP, or Lease?"

NEVER skip the payment method selection for purchases!

Always end with: [Replied by: Raava AI Concierge]"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process with FIXED order creation"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})

        # Get last user message
        last_user_message = ""
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break

        # Initialize
        if not session_context.get("stage"):
            session_context["stage"] = "greeting"
            session_context["preferences"] = {}
            session_context["customer_info"] = {}

        print(f"\n🔍 DEBUG - Current Stage: {session_context.get('stage')}")
        print(f"🔍 DEBUG - User Message: {last_user_message}")
        print(
            f"🔍 DEBUG - Has Vehicle: {bool(session_context.get('selected_vehicle'))}"
        )
        print(f"🔍 DEBUG - Payment Method: {session_context.get('payment_method')}")
        print(
            f"🔍 DEBUG - Customer Email: {session_context.get('customer_info', {}).get('email')}"
        )

        enhanced_context = ""

        # 🔥 FIRST: Check if we should CREATE ORDER
        if self._should_create_order(session_context):
            print("🔥 CREATING ORDER NOW!")
            order_result = self._create_order_now(session_context)

            if order_result.get("success"):
                print(f"✅ ORDER CREATED: {order_result.get('order_id')}")

                # Return order confirmation directly
                return {
                    "messages": [AIMessage(content=order_result["message"])],
                    "context": session_context,
                }
            else:
                print(f"❌ ORDER CREATION FAILED: {order_result.get('message')}")
                enhanced_context += f"\n\n❌ ERROR: {order_result.get('message')}\n"

        # Analyze intent
        intent = self._analyze_intent(last_user_message, session_context)
        print(f"🔍 DEBUG - Intent: {intent}")

        # Handle vehicle search
        if intent["type"] == "vehicle_search":
            vehicles = self._search_vehicles(intent)
            if vehicles:
                session_context["available_vehicles"] = vehicles[:3]
                enhanced_context += "\n\n🔍 VEHICLE SEARCH RESULTS:\n"
                enhanced_context += self._format_vehicles(vehicles[:3])
                session_context["stage"] = "vehicle_selection"  # ✅ Update stage

                print(
                    f"✅ Found {len(vehicles)} vehicles, stage set to: vehicle_selection"
                )

        # Handle vehicle selection
        elif intent["type"] == "vehicle_selection":
            idx = intent.get("vehicle_index")
            if idx is not None and session_context.get("available_vehicles"):
                vehicles = session_context["available_vehicles"]
                if 0 <= idx < len(vehicles):
                    selected = vehicles[idx]
                    session_context["selected_vehicle"] = selected
                    session_context["stage"] = "payment_method_selection"

                    enhanced_context += (
                        f"\n\n✅ VEHICLE SELECTED: {selected['title']}\n"
                    )
                    enhanced_context += f"Price: £{selected.get('price', 0):,}\n"
                    enhanced_context += (
                        f"Mileage: {selected.get('mileage', 0):,} miles\n"
                    )
                    enhanced_context += (
                        "ASK: Would you prefer Cash Payment or Finance Options?\n"
                    )

                    print(f"✅ Vehicle saved to context: {selected['title']}")
                else:
                    enhanced_context += (
                        "\n\n❌ Invalid vehicle selection. Please choose 1, 2, or 3.\n"
                    )

        # Handle payment method selection
        elif intent["type"] == "payment_method":
            payment = intent.get("method")
            session_context["payment_method"] = payment

            if payment == "cash":
                session_context["stage"] = "collecting_customer_info"
                enhanced_context += "\n\n✅ CASH PAYMENT SELECTED\n"
                enhanced_context += "ASK: Name, email, phone?\n"
            elif payment == "finance":
                session_context["stage"] = "finance_type_selection"
                enhanced_context += "\n\n✅ FINANCE SELECTED\n"
                enhanced_context += "ASK: PCP, HP, or Lease?\n"

        # Handle finance type selection
        elif intent["type"] == "finance_type":
            finance_type = intent.get("type")
            session_context["finance_type"] = finance_type
            session_context["stage"] = "collecting_customer_info"

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
                enhanced_context += "\n\nASK: Name, email, phone?\n"

        # Handle customer info
        elif intent["type"] == "customer_info":
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
            else:
                enhanced_context += (
                    "\n\n✅ ALL INFO COLLECTED - READY TO CREATE ORDER\n"
                )
                session_context["stage"] = "ready_to_order"

        # Build conversation
        conversation_messages = [
            SystemMessage(content=self.system_prompt + enhanced_context)
        ]

        for msg in messages[-6:]:
            conversation_messages.append(msg)

        # Get response
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

        # 🔥 Check if LLM said to create order
        if "CREATE_ORDER_NOW" in response_text:
            print("🔥 LLM TRIGGERED ORDER CREATION")
            order_result = self._create_order_now(session_context)

            if order_result.get("success"):
                response_text = order_result["message"]

        # ✅ CRITICAL: Update state with modified context
        state["context"] = session_context

        print(
            f"✅ Returning - Stage: {session_context.get('stage')}, Has Vehicle: {bool(session_context.get('selected_vehicle'))}"
        )

        return {
            "messages": [AIMessage(content=response_text)],
            "context": session_context,
        }

    def _should_create_order(self, context: Dict) -> bool:
        """Check if we have everything needed for order"""
        vehicle = context.get("selected_vehicle")
        payment = context.get("payment_method")
        customer = context.get("customer_info", {})

        # Must have vehicle
        if not vehicle:
            return False

        # Must have payment method
        if not payment:
            return False

        # If finance, must have finance type
        if payment == "finance" and not context.get("finance_type"):
            return False

        # Must have customer details
        if not customer.get("email"):
            return False
        if not customer.get("name"):
            return False

        # Stage must be ready
        if context.get("stage") != "ready_to_order":
            return False

        print("✅ ALL REQUIREMENTS MET FOR ORDER CREATION")
        return True

    def _create_order_now(self, context: Dict) -> Dict[str, Any]:
        """ACTUALLY CREATE ORDER IN DATABASE"""
        try:
            vehicle = context.get("selected_vehicle")
            customer = context.get("customer_info")
            payment_method = context.get("payment_method")
            finance_type = context.get("finance_type")

            print(f"\n🔥 CREATING ORDER:")

            # Validate we have vehicle
            if not vehicle:
                print("❌ No vehicle in context!")
                return {"success": False, "message": "Please select a vehicle first"}

            print(f"   Vehicle: {vehicle.get('title', 'Unknown')}")
            print(f"   Payment: {payment_method}")
            print(f"   Customer: {customer.get('email') if customer else 'Missing'}")

            # Prepare finance details if applicable
            finance_details = None
            if payment_method == "finance" and finance_type:
                options = context.get("finance_options", {})
                key = f"{finance_type}_options"
                if options.get(key):
                    finance_details = options[key][0]
                    print(
                        f"   Finance: {finance_type.upper()} - £{finance_details.get('monthly_payment', 0)}/mo"
                    )

            # CREATE ORDER
            result = order_manager.create_order(
                order_type="purchase",
                vehicle=vehicle,
                customer=customer,
                finance_details=finance_details,
            )

            if result.get("success"):
                order_id = result.get("order_id")
                print(f"✅ ORDER CREATED IN DATABASE: {order_id}")

                # Verify it's in database
                from database import orders_col

                db_order = orders_col.find_one({"order_id": order_id})
                if db_order:
                    print(f"✅ VERIFIED IN ORDERS COLLECTION")
                else:
                    print(f"❌ NOT FOUND IN DATABASE!")

                # Mark order created in context
                context["order_created"] = True
                context["order_id"] = order_id
                context["stage"] = "order_completed"

                return result
            else:
                print(f"❌ ORDER CREATION FAILED: {result.get('message')}")
                return result

        except Exception as e:
            print(f"❌ EXCEPTION IN ORDER CREATION: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"Error: {str(e)}"}

    def _analyze_intent(self, text: str, context: Dict) -> Dict[str, Any]:
        """Analyze user intent - FIXED to prioritize customer info detection"""
        text_lower = text.lower()
        stage = context.get("stage", "")

        # 🔥 FIX: Check for customer info FIRST (before vehicle selection)
        # If message contains email, it's definitely customer info, not a vehicle selection
        if "@" in text:
            print("🔍 Detected customer info (email found)")
            return {"type": "customer_info"}

        # Vehicle search
        for make in LUXURY_MAKES:
            if make.lower() in text_lower:
                return {"type": "vehicle_search", "make": make}

        # 🔥 FIX: Vehicle selection - ONLY check if we're in vehicle_selection stage
        # AND we have available vehicles AND the message doesn't look like customer info
        if stage == "vehicle_selection" and context.get("available_vehicles"):
            # Look for explicit selection patterns first
            match = re.search(
                r"(?:option|take|pick|choose|select|want|fix)\s*([1-3])", text_lower
            )
            if not match:
                # Only match standalone numbers at START of message
                # This prevents matching "1" inside phone numbers like "+919012345672"
                match = re.search(r"^([1-3])\b", text.strip())

            if match:
                vehicle_num = int(match.group(1))
                print(f"🔍 Detected vehicle selection: {vehicle_num}")
                return {"type": "vehicle_selection", "vehicle_index": vehicle_num - 1}

        # Payment method selection
        if stage == "payment_method_selection":
            if any(w in text_lower for w in ["cash", "full", "upfront", "a"]):
                return {"type": "payment_method", "method": "cash"}
            elif any(w in text_lower for w in ["finance", "monthly", "b"]):
                return {"type": "payment_method", "method": "finance"}

        # Finance type selection
        if stage == "finance_type_selection":
            if "pcp" in text_lower or "a" in text_lower:
                return {"type": "finance_type", "type": "pcp"}
            elif "hp" in text_lower or "hire" in text_lower or "b" in text_lower:
                return {"type": "finance_type", "type": "hp"}
            elif "lease" in text_lower or "c" in text_lower:
                return {"type": "finance_type", "type": "lease"}

        # Customer info (phone number patterns or comma-separated values)
        if "+" in text or re.search(r"\d{10,}", text) or text.count(",") >= 2:
            print("🔍 Detected customer info (phone/comma pattern)")
            return {"type": "customer_info"}

        return {"type": "general"}

    def _search_vehicles(self, intent: Dict) -> List[Dict]:
        """Search vehicles"""
        results = []
        query = {}

        if intent.get("make"):
            query["make"] = {"$regex": intent["make"], "$options": "i"}

        print(f"🔍 Searching with query: {query}")

        try:
            local_cars = list(cars_col.find(query).limit(10))
            print(f"🔍 Found {len(local_cars)} cars in local database")

            for car in local_cars:
                vehicle = {
                    "source": "Raava Exclusive",
                    "title": f"{car.get('make')} {car.get('model')} ({car.get('year')})",
                    "make": car.get("make"),
                    "model": car.get("model"),
                    "year": car.get("year"),
                    "price": car.get("price", 0),
                    "mileage": car.get("mileage", 0),
                    "fuel_type": car.get("fuel_type", "Petrol"),
                    "body_type": car.get("body_type", car.get("style", "Coupe")),
                    "location": car.get("location", "UK"),
                }
                results.append(vehicle)
                print(f"   • {vehicle['title']} - £{vehicle['price']:,}")

        except Exception as e:
            print(f"❌ Search error: {e}")
            import traceback

            traceback.print_exc()

        if not results:
            print("⚠️ No vehicles found in database!")
            print("💡 TIP: Run 'python seed_luxury_cars.py' to add sample vehicles")

        return results

    def _format_vehicles(self, vehicles: List[Dict]) -> str:
        """Format vehicles"""
        result = ""
        for i, car in enumerate(vehicles, 1):
            result += f"{i}. {car['title']} - £{car['price']:,}\n"
            result += f"   • {car['mileage']:,} miles • {car['location']}\n\n"
        return result

    def _format_finance(self, options: Dict, finance_type: str) -> str:
        """Format finance"""
        key = f"{finance_type}_options"
        if options.get(key):
            opt = options[key][0]
            return f"Monthly: £{opt['monthly_payment']:,.2f} | Provider: {opt['provider']}\n"
        return ""

    def _extract_customer_info(self, text: str) -> Dict[str, str]:
        """Extract customer info"""
        info = {}

        # Email
        email = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        if email:
            info["email"] = email.group(0)
            print(f"   📧 Email: {info['email']}")

        # Phone - updated pattern to catch international numbers
        phone = re.search(r"(\+?\d{10,15})", text)
        if phone:
            info["phone"] = phone.group(0)
            print(f"   📞 Phone: {info['phone']}")

        # Name - extract words before email/phone, capitalize first letters
        # Remove email and phone from text first
        text_for_name = text
        if email:
            text_for_name = text_for_name.replace(email.group(0), "")
        if phone:
            text_for_name = text_for_name.replace(phone.group(0), "")

        parts = text_for_name.replace(",", " ").split()
        name_candidates = []

        for word in parts:
            # Skip if it's email or phone remnants
            if "@" in word or word.isdigit() or "+" in word:
                continue
            # Skip common words
            if word.lower() in ["my", "name", "is", "email", "phone", "and", "the"]:
                continue
            # Add if it looks like a name
            if len(word) > 1 and word.replace(".", "").isalpha():
                name_candidates.append(word.strip())

        if name_candidates:
            # Take first 2 words as name, capitalize
            name = " ".join(name_candidates[:2])
            # Capitalize each word
            info["name"] = " ".join(word.capitalize() for word in name.split())
            print(f"   👤 Name: {info['name']}")

        return info


# Singleton
phase1_concierge = Phase1Concierge()
