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
=======
Phase 1 Concierge Agent - FIXED: Proper price extraction from Scraped_Cars
Handles pricing.price format: "£29,395"
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from datetime import datetime
import re
import json


class Phase1Concierge:
    """AI Concierge for vehicle purchases - Handles Scraped_Cars data correctly"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
        )

        self.system_prompt = """You are Raava's luxury automotive concierge assistant. 
You help customers find and purchase their dream vehicles with exceptional service.

Your conversation flow:
1. GREETING - Welcome and understand customer's needs
2. VEHICLE SEARCH - Find matching vehicles from inventory
3. VEHICLE SELECTION - Help customer choose specific vehicle
4. PAYMENT METHOD - Ask: cash or financing?
5. CUSTOMER INFO - Collect: name, email, phone
6. ORDER CREATION - Create order IMMEDIATELY (no confirmations)

CRITICAL RULES:
- NEVER repeat questions already answered
- After collecting phone, CREATE ORDER IMMEDIATELY
- Don't ask for vehicle selection again
- Don't ask for payment confirmation again
- Progress forward only, never backward
"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main conversation handler"""
        try:
            context = state.get("context", {})
            messages = state.get("messages", [])
            user_message = messages[-1].content if messages else ""

            # Initialize context if needed
            if not context or not context.get("stage"):
                context = {
                    "stage": "greeting",
                    "available_vehicles": [],
                    "selected_vehicle": None,
                    "payment_method": None,
                    "customer_info": {},
                    "order_created": False,
                    "order_id": None,
                }

            stage = context.get("stage", "greeting")

            print(f"\n🔍 CONCIERGE - Stage: {stage}")
            print(f"💭 User: {user_message}")

            # Check if we have all data needed for order
            if self._has_all_order_data(context) and not context.get("order_created"):
                print("\n🔥 ALL DATA COLLECTED - CREATING ORDER IMMEDIATELY!")
                return self._create_order(state, context)

            # Route to appropriate handler
            if stage == "greeting":
                return self._handle_greeting(state, context, user_message)
            elif stage == "vehicle_search":
                return self._handle_vehicle_search(state, context, user_message)
            elif stage == "vehicle_selection":
                return self._handle_vehicle_selection(state, context, user_message)
            elif stage == "payment_method":
                return self._handle_payment_method(state, context, user_message)
            elif stage == "selecting_finance_type":
                return self._handle_finance_type_selection(state, context, user_message)
            elif stage == "collecting_name":
                return self._handle_name_collection(state, context, user_message)
            elif stage == "collecting_email":
                return self._handle_email_collection(state, context, user_message)
            elif stage == "collecting_phone":
                return self._handle_phone_collection(state, context, user_message)
            elif stage == "order_confirmed":
                return self._handle_post_order(state, context, user_message)
            else:
                return self._handle_greeting(state, context, user_message)

        except Exception as e:
            print(f"❌ Error in concierge: {e}")
            import traceback

            traceback.print_exc()

            return {
                "messages": [
                    AIMessage(
                        content="I apologize, there was an error. Let me help you from the beginning. What vehicle are you interested in?"
                    )
                ],
                "context": {"stage": "greeting"},
            }

    def _extract_price_from_string(self, price_str: str) -> int:
        """
        Extract numeric price from string format like "£29,395"
        Returns integer price value
        """
        if not price_str:
            return 0

        # Handle if already an integer
        if isinstance(price_str, int):
            return price_str

        # Remove £, commas, spaces and extract digits
        cleaned = price_str.replace("£", "").replace(",", "").replace(" ", "").strip()

        try:
            # Handle decimal points (e.g., "29395.50" -> 29395)
            if "." in cleaned:
                cleaned = cleaned.split(".")[0]
            return int(cleaned) if cleaned.isdigit() else 0
        except:
            print(f"⚠️ Failed to parse price: {price_str}")
            return 0

    def _extract_vehicle_data(self, vehicle: Dict) -> Dict[str, Any]:
        """
        Extract vehicle data from Scraped_Cars format
        Handles: title, subtitle, pricing.price, overview fields
        Returns normalized data with INTEGER price
        """
        data = {}

        # Extract title (e.g., "Vauxhall Frontera Electric")
        data["title"] = vehicle.get("title", "")
        data["subtitle"] = vehicle.get("subtitle", "")

        # Extract make and model from title
        if data["title"]:
            parts = data["title"].strip().split()
            data["make"] = parts[0] if parts else "Unknown"
            data["model"] = " ".join(parts[1:]) if len(parts) > 1 else "Unknown"
        else:
            data["make"] = vehicle.get("make", "Unknown")
            data["model"] = vehicle.get("model", "Unknown")

        # Build full title
        data["full_title"] = data["title"]
        if data["subtitle"]:
            data["full_title"] += f" - {data['subtitle']}"

        # 🔥 CRITICAL: Extract price from pricing.price string
        pricing = vehicle.get("pricing", {})
        if isinstance(pricing, dict):
            price_str = pricing.get("price", "£0")
            data["price"] = self._extract_price_from_string(price_str)
            data["rrp"] = self._extract_price_from_string(pricing.get("rrp", "£0"))
            data["savings"] = pricing.get("savings", "")
            data["status"] = pricing.get("status", "")
        else:
            # Fallback to direct price field
            data["price"] = vehicle.get("price", 0)
            if isinstance(data["price"], str):
                data["price"] = self._extract_price_from_string(data["price"])

        # Extract overview data
        overview = vehicle.get("overview", {})

        # Year - extract from overview or status
        data["year"] = vehicle.get("year", "")
        if not data["year"] and overview:
            # Check if brand new
            if "new" in data.get("status", "").lower():
                data["year"] = "Brand New"
            else:
                data["year"] = "Used"

        # Mileage - extract from overview
        mileage_str = overview.get("Mileage", "0")
        if isinstance(mileage_str, str):
            # Extract just the number (e.g., "5 miles" -> 5)
            mileage_cleaned = "".join(filter(str.isdigit, mileage_str))
            data["mileage"] = int(mileage_cleaned) if mileage_cleaned else 0
        else:
            data["mileage"] = vehicle.get("mileage", 0)

        # Other fields from overview
        data["fuel_type"] = overview.get("Fuel type", "Petrol")
        data["body_type"] = overview.get("Body type", "Unknown")
        data["range"] = overview.get("Range", "")
        data["gearbox"] = overview.get("Gearbox", "")
        data["doors"] = overview.get("Doors", "")
        data["seats"] = overview.get("Seats", "")
        data["colour"] = overview.get("Body colour", "")

        # Additional fields
        data["url"] = vehicle.get("url", "")
        data["images"] = vehicle.get("images", [])
        data["source"] = "AutoTrader"

        return data

    def _handle_greeting(self, state, context, user_message):
        """Handle initial greeting and vehicle inquiry"""
        brands = [
            "vauxhall",
            "lamborghini",
            "ferrari",
            "porsche",
            "mclaren",
            "aston martin",
            "bentley",
            "rolls royce",
            "mercedes",
            "bmw",
            "audi",
            "range rover",
            "jaguar",
            "maserati",
            "bugatti",
        ]

        user_lower = user_message.lower()
        mentioned_brand = None

        for brand in brands:
            if brand in user_lower:
                mentioned_brand = brand
                break

        if mentioned_brand:
            vehicles = self._search_vehicles(mentioned_brand)

            if vehicles:
                context["available_vehicles"] = vehicles
                context["stage"] = "vehicle_selection"

                vehicle_list = self._format_vehicle_list(vehicles)
                response = f"Excellent choice! I found {len(vehicles)} {mentioned_brand.title()} vehicle(s) in our collection:\n\n{vehicle_list}\n\nWhich vehicle interests you? (Please enter the number)"

                return {"messages": [AIMessage(content=response)], "context": context}
            else:
                response = f"I don't currently have {mentioned_brand.title()} vehicles in stock, but I can show you similar luxury vehicles. What style are you interested in?"
        else:
            response = "Welcome to Raava! I'm here to help you find your perfect luxury vehicle. What brand or type of vehicle are you interested in?"

        return {"messages": [AIMessage(content=response)], "context": context}

    def _format_vehicle_list(self, vehicles: List[Dict]) -> str:
        """Format vehicle list with CORRECT price display"""
        formatted = []

        for i, vehicle in enumerate(vehicles, 1):
            # Extract normalized data
            data = self._extract_vehicle_data(vehicle)

            # Build display line
            line = f"{i}. **{data['full_title']}** ({data['year']})\n"
            line += f"   Price: £{data['price']:,}"

            # Add mileage if available
            if data["mileage"] > 0:
                line += f" | Mileage: {data['mileage']:,} miles"

            # Add range for electric vehicles
            if data.get("range"):
                line += f" | Range: {data['range']}"

            formatted.append(line)

        return "\n\n".join(formatted)

    def _handle_vehicle_search(self, state, context, user_message):
        """Handle vehicle search"""
        return self._handle_greeting(state, context, user_message)

    def _handle_vehicle_selection(self, state, context, user_message):
        """Handle vehicle selection from list"""
        available_vehicles = context.get("available_vehicles", [])

        if not available_vehicles:
            return self._handle_greeting(state, context, user_message)

        selection = self._extract_number(user_message)

        if selection and 1 <= selection <= len(available_vehicles):
            selected_vehicle = available_vehicles[selection - 1]
            context["selected_vehicle"] = selected_vehicle
            context["stage"] = "payment_method"

            # Extract data for display
            data = self._extract_vehicle_data(selected_vehicle)

            response = f"""Perfect choice! You've selected:

**{data['full_title']} ({data['year']})**
Price: £{data['price']:,}

How would you like to pay?
1. Full Cash Payment
2. Finance Options (HP, PCP, Lease)

Please let me know your preference."""

            return {"messages": [AIMessage(content=response)], "context": context}
        else:
            response = f"Please enter a number between 1 and {len(available_vehicles)} to select a vehicle."
            return {"messages": [AIMessage(content=response)], "context": context}

    def _handle_payment_method(self, state, context, user_message):
        """Handle payment method selection"""
        user_lower = user_message.lower()

        if "cash" in user_lower or "1" in user_message:
            context["payment_method"] = "cash"
            context["stage"] = "collecting_name"
            response = "Excellent. Full cash payment selected. To proceed with your order, I'll need a few details.\n\nWhat's your full name?"

        elif "finance" in user_lower or "2" in user_message:
            context["payment_method"] = "finance"
            context["stage"] = "selecting_finance_type"

            # Get vehicle price for finance calculation
            selected_vehicle = context.get("selected_vehicle", {})
            vehicle_data = self._extract_vehicle_data(selected_vehicle)
            vehicle_price = vehicle_data["price"]

            # Only calculate finance if price is valid
            if vehicle_price > 0:
                from uk_finance_calculator import uk_finance_calculator

                finance_options = uk_finance_calculator.calculate_all_options(
                    vehicle_price=vehicle_price, deposit_percent=10, term_months=48
                )

                context["finance_options"] = finance_options

                response = f"""Perfect! Here are your finance options for £{vehicle_price:,}:

**1. PCP (Personal Contract Purchase)** - Lowest Monthly Payments
   • Monthly: £{finance_options['pcp_options'][0]['monthly_payment']:,.2f}
   • Optional final payment: £{finance_options['pcp_options'][0]['balloon_payment']:,.2f}
   • {finance_options['pcp_options'][0]['description']}

**2. HP (Hire Purchase)** - Own the Car
   • Monthly: £{finance_options['hp_options'][0]['monthly_payment']:,.2f}
   • Total: £{finance_options['hp_options'][0]['total_cost']:,.2f}
   • {finance_options['hp_options'][0]['description']}

**3. Lease (PCH)** - Never Own, Just Drive
   • Monthly: £{finance_options['lease_options'][0]['monthly_payment']:,.2f}
   • {finance_options['lease_options'][0]['description']}

Which option works best for you? (Enter 1, 2, or 3)"""
            else:
                response = "I apologize, but I'm unable to calculate finance for this vehicle. Let's proceed with cash payment. What's your full name?"
                context["payment_method"] = "cash"
                context["stage"] = "collecting_name"

            return {"messages": [AIMessage(content=response)], "context": context}
        else:
            response = "Please choose:\n1. Full Cash Payment\n2. Finance Options\n\nJust reply with '1' or '2', or 'cash' or 'finance'."
            return {"messages": [AIMessage(content=response)], "context": context}

        return {"messages": [AIMessage(content=response)], "context": context}

    def _handle_finance_type_selection(self, state, context, user_message):
        """Handle finance type selection (PCP/HP/Lease)"""
        user_lower = user_message.lower()
        selection = self._extract_number(user_message)

        finance_options = context.get("finance_options", {})

        if selection == 1 or "pcp" in user_lower:
            context["finance_type"] = "PCP"
            context["selected_finance"] = (
                finance_options["pcp_options"][0] if finance_options else None
            )
            context["stage"] = "collecting_name"

            pcp = finance_options["pcp_options"][0]
            response = f"""Great choice! PCP selected.

Monthly Payment: £{pcp['monthly_payment']:,.2f}
Optional Final Payment: £{pcp['balloon_payment']:,.2f}
Term: {pcp['term_months']} months
APR: {pcp['apr']}%

To proceed with your order, what's your full name?"""

        elif selection == 2 or "hp" in user_lower:
            context["finance_type"] = "HP"
            context["selected_finance"] = (
                finance_options["hp_options"][0] if finance_options else None
            )
            context["stage"] = "collecting_name"

            hp = finance_options["hp_options"][0]
            response = f"""Perfect! HP (Hire Purchase) selected.

Monthly Payment: £{hp['monthly_payment']:,.2f}
Total Cost: £{hp['total_cost']:,.2f}
Term: {hp['term_months']} months
APR: {hp['apr']}%

To proceed with your order, what's your full name?"""

        elif selection == 3 or "lease" in user_lower or "pch" in user_lower:
            context["finance_type"] = "Lease"
            context["selected_finance"] = (
                finance_options["lease_options"][0] if finance_options else None
            )
            context["stage"] = "collecting_name"

            lease = finance_options["lease_options"][0]
            response = f"""Excellent! Lease (PCH) selected.

Monthly Payment: £{lease['monthly_payment']:,.2f}
Term: {lease['term_months']} months

To proceed with your order, what's your full name?"""

        else:
            response = "Please choose:\n1. PCP\n2. HP\n3. Lease\n\nJust reply with '1', '2', or '3'."
            return {"messages": [AIMessage(content=response)], "context": context}

        return {"messages": [AIMessage(content=response)], "context": context}

    def _handle_name_collection(self, state, context, user_message):
        """Collect customer name"""
        name = user_message.strip()

        if len(name) >= 2:
            if "customer_info" not in context:
                context["customer_info"] = {}
            context["customer_info"]["name"] = name
            context["stage"] = "collecting_email"
            response = f"Perfect, {name}. What's the best email address to reach you?"

            if self._has_all_order_data(context):
                return self._create_order(state, context)

            return {"messages": [AIMessage(content=response)], "context": context}
        else:
            response = "Please provide your full name."
            return {"messages": [AIMessage(content=response)], "context": context}

    def _handle_email_collection(self, state, context, user_message):
        """Collect customer email"""
        email = self._extract_email(user_message)

        if email:
            if "customer_info" not in context:
                context["customer_info"] = {}
            context["customer_info"]["email"] = email
            context["stage"] = "collecting_phone"
            response = f"Perfect. What's the best phone number to reach you?"

            if self._has_all_order_data(context):
                return self._create_order(state, context)

            return {"messages": [AIMessage(content=response)], "context": context}
        else:
            response = "Please provide a valid email address."
            return {"messages": [AIMessage(content=response)], "context": context}

    def _handle_phone_collection(self, state, context, user_message):
        """Collect phone and CREATE ORDER IMMEDIATELY"""
        phone = self._extract_phone(user_message)

        if phone:
            if "customer_info" not in context:
                context["customer_info"] = {}
            context["customer_info"]["phone"] = phone

            print("\n🔥 PHONE COLLECTED - CREATING ORDER IMMEDIATELY!")
            return self._create_order(state, context)
        else:
            response = "Please provide a valid phone number (e.g., +44 123 456 7890 or 07123456789)."
            return {"messages": [AIMessage(content=response)], "context": context}

    def _has_all_order_data(self, context: Dict) -> bool:
        """Check if we have all data needed to create order"""
        customer_info = context.get("customer_info", {})

        has_vehicle = bool(context.get("selected_vehicle"))
        has_payment = bool(context.get("payment_method"))
        has_name = bool(customer_info.get("name"))
        has_email = bool(customer_info.get("email"))
        has_phone = bool(customer_info.get("phone"))

        return has_vehicle and has_payment and has_name and has_email and has_phone

    def _create_order(self, state, context):
        """CREATE ORDER IN DATABASE"""
        print("\n" + "=" * 70)
        print("📋 CREATING ORDER")
        print("=" * 70)

        selected_vehicle = context.get("selected_vehicle")
        payment_method = context.get("payment_method", "cash")
        customer_info = context.get("customer_info", {})

        # Extract normalized vehicle data with CORRECT PRICE
        vehicle_data = self._extract_vehicle_data(selected_vehicle)

        print(f"\n📊 Extracted Vehicle Data:")
        print(f"   Make: {vehicle_data['make']}")
        print(f"   Model: {vehicle_data['model']}")
        print(f"   Year: {vehicle_data['year']}")
        print(f"   Price: £{vehicle_data['price']:,}")
        print(f"   Mileage: {vehicle_data['mileage']:,}")

        # Validate price
        if vehicle_data["price"] == 0:
            print("❌ WARNING: Price is 0! Check price extraction")
            return {
                "messages": [
                    AIMessage(
                        content="I apologize, there was an issue with the vehicle pricing. Please contact support@raava.com"
                    )
                ],
                "context": context,
            }

        # Create normalized vehicle object for order
        normalized_vehicle = {
            "make": vehicle_data["make"],
            "model": vehicle_data["model"],
            "year": vehicle_data["year"],
            "price": vehicle_data["price"],  # This is now an INTEGER
            "mileage": vehicle_data["mileage"],
            "title": vehicle_data["full_title"],
            "subtitle": vehicle_data["subtitle"],
            "fuel_type": vehicle_data["fuel_type"],
            "body_type": vehicle_data["body_type"],
            "source": "AutoTrader (Scraped)",
            "url": vehicle_data["url"],
            "images": vehicle_data["images"],
        }

        # Prepare customer data
        customer_data = {
            "name": customer_info.get("name"),
            "email": customer_info.get("email"),
            "phone": customer_info.get("phone"),
            "address": customer_info.get("address", ""),
            "postcode": customer_info.get("postcode", ""),
            "session_id": state.get("session_id", ""),
        }

        # Prepare finance details if needed
        finance_details = None
        if payment_method and payment_method.lower() not in ["cash", "full cash"]:
            selected_finance = context.get("selected_finance")
            if selected_finance:
                finance_details = {
                    "type": context.get("finance_type", "HP"),
                    "provider": selected_finance.get("provider", "Raava Finance"),
                    "monthly_payment": selected_finance.get("monthly_payment", 0),
                    "deposit_amount": vehicle_data["price"] * 0.1,
                    "term_months": selected_finance.get("term_months", 48),
                    "apr": selected_finance.get("apr", 9.9),
                    "total_cost": selected_finance.get(
                        "total_cost", vehicle_data["price"]
                    ),
                    "balloon_payment": selected_finance.get("balloon_payment", 0),
                }

        # CREATE ORDER
        try:
            from order_manager import order_manager

            print(f"\n🚀 Calling order_manager.create_order()...")

            order_result = order_manager.create_order(
                order_type="purchase",
                vehicle=normalized_vehicle,
                customer=customer_data,
                finance_details=finance_details,
            )

            if order_result.get("success"):
                order_id = order_result.get("order_id")
                order_message = order_result.get("message")

                print(f"\n✅ ORDER CREATED: {order_id}")

                context["order_created"] = True
                context["order_id"] = order_id
                context["stage"] = "order_confirmed"

                return {
                    "messages": [AIMessage(content=order_message)],
                    "context": context,
                }
            else:
                error_message = order_result.get("message", "Unknown error")
                print(f"\n❌ ORDER FAILED: {error_message}")

                return {
                    "messages": [
                        AIMessage(
                            content=f"I apologize, but there was an issue creating your order. Error: {error_message}. Please contact support@raava.com"
                        )
                    ],
                    "context": context,
                }

        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")
            import traceback

            traceback.print_exc()

            return {
                "messages": [
                    AIMessage(
                        content="I apologize, there was a technical issue. Please contact support@raava.com"
                    )
                ],
                "context": context,
            }

    def _handle_post_order(self, state, context, user_message):
        """Handle conversation after order"""
        response = """Your order has been confirmed! 

Would you like to:
1. Start a new vehicle search
2. Contact our team
3. View finance options"""

        return {"messages": [AIMessage(content=response)], "context": context}

    def _search_vehicles(self, brand: str) -> List[Dict]:
        """Search vehicles in Scraped_Cars collection"""
        try:
            from database import db

            # Use Scraped_Cars collection
            scraped_cars_col = db["Scraped_Cars"]

            query = {
                "$or": [
                    {"make": {"$regex": brand, "$options": "i"}},
                    {"model": {"$regex": brand, "$options": "i"}},
                    {"title": {"$regex": brand, "$options": "i"}},
                ]
            }

            vehicles = list(scraped_cars_col.find(query).limit(10))

            for v in vehicles:
                v["_id"] = str(v["_id"])

            print(f"\n🔍 Found {len(vehicles)} vehicles matching '{brand}'")
            if vehicles:
                # Debug: Show first vehicle's pricing
                first = vehicles[0]
                pricing = first.get("pricing", {})
                print(f"   Sample: {first.get('title', 'No title')}")
                print(f"   Pricing: {pricing}")

            return vehicles

        except Exception as e:
            print(f"Error searching vehicles: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _extract_number(self, text: str) -> int:
        """Extract number from text"""
        numbers = re.findall(r"\d+", text)
        return int(numbers[0]) if numbers else None

    def _extract_email(self, text: str) -> str:
        """Extract email from text"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None

    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        cleaned = re.sub(r"[^\d+]", "", text)
        if len(cleaned) >= 10:
            return text.strip()
        return None



# Singleton
phase1_concierge = Phase1Concierge()
