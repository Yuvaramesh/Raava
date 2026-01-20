"""
Phase 1 Concierge Agent - FIXED: Async support + No repeated questions
Creates order IMMEDIATELY after collecting phone number
"""

from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from datetime import datetime
import re
import json


class Phase1Concierge:
    """AI Concierge for vehicle purchases - Creates orders WITHOUT repeated questions"""

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

Current conversation stage will be tracked in context.
"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main conversation handler with IMMEDIATE ORDER CREATION"""

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
            print(f"🚗 Vehicle: {bool(context.get('selected_vehicle'))}")
            print(f"💳 Payment: {context.get('payment_method')}")
            print(f"👤 Customer: {context.get('customer_info')}")

            # 🔥 CRITICAL FIX: Check if we have all data needed for order
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

    def _has_all_order_data(self, context: Dict) -> bool:
        """Check if we have all data needed to create order"""
        customer_info = context.get("customer_info", {})

        has_vehicle = bool(context.get("selected_vehicle"))
        has_payment = bool(context.get("payment_method"))
        has_name = bool(customer_info.get("name"))
        has_email = bool(customer_info.get("email"))
        has_phone = bool(customer_info.get("phone"))

        all_data = has_vehicle and has_payment and has_name and has_email and has_phone

        print(f"\n📊 ORDER DATA CHECK:")
        print(f"   ✓ Vehicle: {has_vehicle}")
        print(f"   ✓ Payment: {has_payment}")
        print(f"   ✓ Name: {has_name}")
        print(f"   ✓ Email: {has_email}")
        print(f"   ✓ Phone: {has_phone}")
        print(f"   {'✅ ALL DATA READY' if all_data else '⏳ WAITING FOR MORE DATA'}")

        return all_data

    def _handle_greeting(self, state, context, user_message):
        """Handle initial greeting and vehicle inquiry"""
        brands = [
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
            "vauxhall",
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
                response = f"I don't currently have {mentioned_brand.title()} vehicles in stock, but I can show you similar luxury vehicles. What style are you interested in? (SUV, Sedan, Coupe, etc.)"
        else:
            response = "Welcome to Raava! I'm here to help you find your perfect luxury vehicle. What brand or type of vehicle are you interested in?"

        return {"messages": [AIMessage(content=response)], "context": context}

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

            vehicle_title = selected_vehicle.get(
                "title",
                f"{selected_vehicle.get('make')} {selected_vehicle.get('model')}",
            )
            price = selected_vehicle.get("price", 0)

            response = f"""Perfect choice! You've selected:

**{vehicle_title}**
Price: £{price:,}

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

        elif (
            "finance" in user_lower
            or "2" in user_message
            or "hp" in user_lower
            or "pcp" in user_lower
        ):
            context["payment_method"] = "finance"
            context["finance_type"] = "HP"
            context["stage"] = "collecting_name"
            response = "Great! We offer excellent finance options. I'll arrange for our finance team to contact you with the best rates.\n\nTo proceed, what's your full name?"
        else:
            response = "Please choose:\n1. Full Cash Payment\n2. Finance Options\n\nJust reply with '1' or '2', or 'cash' or 'finance'."
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

            # 🔥 Check if we have all data after this update
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

            # 🔥 Check if we have all data after this update
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

            # 🔥 IMMEDIATELY CREATE ORDER - NO QUESTIONS
            print("\n🔥 PHONE COLLECTED - CREATING ORDER IMMEDIATELY!")
            return self._create_order(state, context)
        else:
            response = "Please provide a valid phone number (e.g., +44 123 456 7890 or 07123456789)."
            return {"messages": [AIMessage(content=response)], "context": context}

    def _create_order(self, state, context):
        """CREATE ORDER IN DATABASE - No repeated questions"""
        print("\n" + "=" * 70)
        print("📋 CREATING ORDER - FINAL DATA CHECK")
        print("=" * 70)

        selected_vehicle = context.get("selected_vehicle")
        payment_method = context.get("payment_method", "cash")
        customer_info = context.get("customer_info", {})

        name = customer_info.get("name")
        email = customer_info.get("email")
        phone = customer_info.get("phone")

        # Final validation
        if not selected_vehicle or not name or not email or not phone:
            print("❌ Missing data!")
            print(f"   Vehicle: {bool(selected_vehicle)}")
            print(f"   Name: {name}")
            print(f"   Email: {email}")
            print(f"   Phone: {phone}")

            return {
                "messages": [
                    AIMessage(
                        content="I'm missing some information. Let's start over. What vehicle are you interested in?"
                    )
                ],
                "context": {"stage": "greeting"},
            }

        print(f"✅ All data present:")
        print(
            f"   Vehicle: {selected_vehicle.get('make')} {selected_vehicle.get('model')}"
        )
        print(f"   Customer: {name} ({email}, {phone})")
        print(f"   Payment: {payment_method}")

        # Prepare customer data
        customer_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": customer_info.get("address", ""),
            "postcode": customer_info.get("postcode", ""),
            "session_id": state.get("session_id", ""),
        }

        # Prepare finance details
        finance_details = None
        if payment_method and payment_method.lower() not in ["cash", "full cash"]:
            vehicle_price = selected_vehicle.get("price", 0)
            finance_details = {
                "type": context.get("finance_type", "HP"),
                "provider": "Raava Finance",
                "monthly_payment": vehicle_price * 0.02,
                "deposit_amount": vehicle_price * 0.1,
                "term_months": 48,
                "apr": 9.9,
                "total_cost": vehicle_price * 1.2,
            }

        # CREATE ORDER
        try:
            from order_manager import order_manager

            print(f"\n🚀 Calling order_manager.create_order()...")

            order_result = order_manager.create_order(
                order_type="purchase",
                vehicle=selected_vehicle,
                customer=customer_data,
                finance_details=finance_details,
            )

            if order_result.get("success"):
                order_id = order_result.get("order_id")
                order_message = order_result.get("message")

                print(f"\n✅ ORDER CREATED: {order_id}")

                # Update context
                context["order_created"] = True
                context["order_id"] = order_id
                context["stage"] = "order_confirmed"

                print("=" * 70 + "\n")

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

    # Helper functions
    def _search_vehicles(self, brand: str) -> List[Dict]:
        """Search vehicles in database"""
        try:
            from database import cars_col

            query = {
                "$or": [
                    {"make": {"$regex": brand, "$options": "i"}},
                    {"model": {"$regex": brand, "$options": "i"}},
                    {"title": {"$regex": brand, "$options": "i"}},
                ]
            }

            vehicles = list(cars_col.find(query).limit(10))

            for v in vehicles:
                v["_id"] = str(v["_id"])

            return vehicles

        except Exception as e:
            print(f"Error searching vehicles: {e}")
            return []

    def _format_vehicle_list(self, vehicles: List[Dict]) -> str:
        """Format vehicle list"""
        formatted = []

        for i, vehicle in enumerate(vehicles, 1):
            title = vehicle.get(
                "title", f"{vehicle.get('make')} {vehicle.get('model')}"
            )
            year = vehicle.get("year", "")
            price = vehicle.get("price", 0)
            mileage = vehicle.get("mileage", 0)

            line = f"{i}. **{title}** ({year})\n   Price: £{price:,} | Mileage: {mileage:,} miles"
            formatted.append(line)

        return "\n\n".join(formatted)

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
