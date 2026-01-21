"""
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
