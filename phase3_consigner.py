"""
Raava AI Consigner - Phase 3 SIMPLIFIED
Help users sell their vehicles with minimal questions
Only asks: Make, Model, Year, Color, Mileage, Reason for Sale
"""

import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import OPENAI_API_KEY, LLM_MODEL_NAME
from datetime import datetime
import re


class Phase3Consigner:
    """
    Raava AI Consigner - Vehicle selling specialist (SIMPLIFIED)
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava AI Consigner - professional vehicle listing specialist.

🎯 MISSION: Help customers sell their vehicles with professional listings

💬 SIMPLIFIED CONVERSATION FLOW - Ask ONLY these questions:

1. **VEHICLE MAKE**: What make is your car? (e.g., Lamborghini, Ferrari, Porsche)
2. **MODEL**: What model? (e.g., Huracan Evo, 488 GTB, 911 Turbo)
3. **YEAR**: What year?
4. **COLOR**: What color is the car?
5. **MILEAGE**: Current mileage?
6. **REASON FOR SALE**: Why are you selling?

That's it! Don't ask about:
- Service history (we'll note "Available on request")
- Specifications (we'll use standard specs for the model)
- Photos (we'll note "Professional photography available")
- Condition details (we'll use general "Excellent condition")
- Marketplaces (we'll default to AutoTrader)
- Valuation (we'll provide estimate based on make/model/year)

After getting these 6 items, immediately move to owner contact details (name, email, phone)

🔑 CRITICAL LISTING CREATION RULES:

When you have ALL of these 6 core details:
✅ Make
✅ Model  
✅ Year
✅ Color
✅ Mileage
✅ Reason for sale
✅ Owner contact (name, email, phone)

Then you MUST respond with EXACTLY this format:

"CREATE_LISTING_NOW

Vehicle: [make model year color]
Mileage: [mileage]
Reason: [reason for sale]
Owner: [name, email, phone]"

This triggers the listing creation system.

DEFAULT VALUES TO USE:
- Marketplaces: AutoTrader (default)
- Service History: "Available on request"
- Photos: "Professional photography available"
- Condition: "Excellent condition throughout"
- Asking Price: Calculate from year/mileage (provide estimate)

Always end with: [Replied by: Raava AI Consigner]"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process consignment request"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})

        # Get last user message
        last_user_message = ""
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break

        # Initialize consigner context
        if not session_context.get("consigner_stage"):
            session_context = self._initialize_consigner_context(session_context)

        print(f"\n📸 CONSIGNER - Stage: {session_context.get('consigner_stage')}")
        print(f"📝 User: {last_user_message}")

        # Extract consigner-specific context
        consigner_context = self._extract_consigner_context(session_context)

        enhanced_context = ""

        # Check if we should CREATE LISTING
        if self._should_create_listing(consigner_context):
            print("🔥 CREATING LISTING NOW!")
            listing_result = self._create_listing_now(consigner_context)

            if listing_result.get("success"):
                print(f"✅ LISTING CREATED: {listing_result.get('listing_id')}")

                # Update context
                consigner_context["listing_created"] = True
                consigner_context["listing_id"] = listing_result.get("listing_id")
                consigner_context["consigner_stage"] = "listing_completed"

                # Save back to session
                self._save_consigner_context(session_context, consigner_context)

                return {
                    "messages": [AIMessage(content=listing_result["message"])],
                    "context": session_context,
                }
            else:
                print(f"❌ LISTING CREATION FAILED: {listing_result.get('message')}")
                enhanced_context += f"\n\n❌ ERROR: {listing_result.get('message')}\n"

        # Analyze intent
        intent = self._analyze_intent(last_user_message, consigner_context)
        print(f"🔍 Intent: {intent['type']}")

        # Handle vehicle make
        if (
            intent["type"] == "vehicle_make"
            or consigner_context.get("consigner_stage") == "vehicle_make"
        ):
            extracted = self._extract_vehicle_make(last_user_message)
            if extracted:
                consigner_context["vehicle_details"]["make"] = extracted
                consigner_context["consigner_stage"] = "vehicle_model"
                enhanced_context += f"\n\n✅ MAKE: {extracted}\n"
                enhanced_context += "ASK: What model?\n"

        # Handle model
        elif (
            intent["type"] == "vehicle_model"
            or consigner_context.get("consigner_stage") == "vehicle_model"
        ):
            model = last_user_message.strip()
            consigner_context["vehicle_details"]["model"] = model
            consigner_context["consigner_stage"] = "vehicle_year"
            enhanced_context += f"\n\n✅ MODEL: {model}\n"
            enhanced_context += "ASK: What year?\n"

        # Handle year
        elif (
            intent["type"] == "vehicle_year"
            or consigner_context.get("consigner_stage") == "vehicle_year"
        ):
            year = self._extract_year(last_user_message)
            if year:
                consigner_context["vehicle_details"]["year"] = year
                consigner_context["consigner_stage"] = "vehicle_color"
                enhanced_context += f"\n\n✅ YEAR: {year}\n"
                enhanced_context += "ASK: What color is the car?\n"

        # Handle color
        elif (
            intent["type"] == "vehicle_color"
            or consigner_context.get("consigner_stage") == "vehicle_color"
        ):
            color = last_user_message.strip()
            consigner_context["vehicle_details"]["color"] = color
            consigner_context["consigner_stage"] = "vehicle_mileage"
            enhanced_context += f"\n\n✅ COLOR: {color}\n"
            enhanced_context += "ASK: Current mileage?\n"

        # Handle mileage
        elif (
            intent["type"] == "vehicle_mileage"
            or consigner_context.get("consigner_stage") == "vehicle_mileage"
        ):
            mileage = self._extract_mileage(last_user_message)
            if mileage:
                consigner_context["vehicle_details"]["mileage"] = mileage
                consigner_context["consigner_stage"] = "reason_for_sale"
                enhanced_context += f"\n\n✅ MILEAGE: {mileage:,} miles\n"
                enhanced_context += "ASK: Why are you selling?\n"

        # Handle reason for sale
        elif (
            intent["type"] == "reason_for_sale"
            or consigner_context.get("consigner_stage") == "reason_for_sale"
        ):
            reason = last_user_message.strip()
            consigner_context["reason_for_sale"] = reason
            consigner_context["consigner_stage"] = "owner_details"

            # Calculate asking price estimate
            valuation = self._calculate_valuation(consigner_context)
            consigner_context["valuation"] = valuation
            consigner_context["asking_price"] = valuation.get("private_sale", 0)

            enhanced_context += f"\n\n✅ REASON FOR SALE: {reason}\n"
            enhanced_context += (
                f"💰 ESTIMATED VALUE: £{valuation.get('private_sale', 0):,}\n"
            )
            enhanced_context += "ASK: Your name, email, and phone for listing?\n"

        # Handle owner details
        elif intent["type"] == "owner_details":
            owner_info = self._extract_owner_details(last_user_message)
            consigner_context["owner_details"] = owner_info

            missing = self._check_owner_details(owner_info)
            if not missing:
                consigner_context["consigner_stage"] = "ready_to_list"
                enhanced_context += "\n\n✅ OWNER DETAILS COLLECTED\n"
                enhanced_context += "READY TO CREATE LISTING\n"
            else:
                enhanced_context += f"\n\n📋 Still need: {', '.join(missing)}\n"

        # Save context
        self._save_consigner_context(session_context, consigner_context)

        # Build conversation
        conversation_messages = [
            SystemMessage(content=self.system_prompt + enhanced_context)
        ]

        for msg in messages[-6:]:
            conversation_messages.append(msg)

        # Get response
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

        # Check if LLM said to create listing
        if "CREATE_LISTING_NOW" in response_text:
            print("🔥 LLM TRIGGERED LISTING CREATION")
            listing_result = self._create_listing_now(consigner_context)

            if listing_result.get("success"):
                response_text = listing_result["message"]
                consigner_context["listing_created"] = True
                consigner_context["listing_id"] = listing_result.get("listing_id")
                self._save_consigner_context(session_context, consigner_context)

        print(
            f"✅ Consigner returning - Stage: {consigner_context.get('consigner_stage')}"
        )

        return {
            "messages": [AIMessage(content=response_text)],
            "context": session_context,
        }

    def _initialize_consigner_context(self, context: Dict) -> Dict:
        """Initialize consigner-specific fields"""
        return {
            "session_id": context.get("session_id"),
            "routed": context.get("routed", True),
            "active_agent": "phase3_consigner",
            "consigner_stage": "vehicle_make",
            "vehicle_details": {},
            "reason_for_sale": "",
            "owner_details": {},
            "listing_created": False,
            "listing_id": None,
            # Use defaults for optional fields
            "service_history": {
                "description": "Available on request",
                "full_history": True,
            },
            "specifications": {"description": "Standard manufacturer specifications"},
            "condition": {"rating": 9, "notes": "Excellent condition throughout"},
            "photos_ready": True,
            "marketplaces": ["AutoTrader"],
            "asking_price": 0,  # Will be calculated
        }

    def _extract_consigner_context(self, context: Dict) -> Dict:
        """Extract ONLY consigner-related fields"""
        return {
            "session_id": context.get("session_id"),
            "consigner_stage": context.get("consigner_stage", "vehicle_make"),
            "vehicle_details": context.get("vehicle_details", {}),
            "reason_for_sale": context.get("reason_for_sale", ""),
            "service_history": context.get("service_history", {}),
            "specifications": context.get("specifications", {}),
            "condition": context.get("condition", {}),
            "photos_ready": context.get("photos_ready", False),
            "valuation": context.get("valuation", {}),
            "asking_price": context.get("asking_price", 0),
            "marketplaces": context.get("marketplaces", []),
            "owner_details": context.get("owner_details", {}),
            "listing_created": context.get("listing_created", False),
            "listing_id": context.get("listing_id"),
        }

    def _save_consigner_context(self, session_context: Dict, consigner_context: Dict):
        """Save consigner context back to session"""
        session_context.update(consigner_context)

    def _should_create_listing(self, context: Dict) -> bool:
        """Check if ready to create listing - simplified check"""
        vehicle = context.get("vehicle_details", {})
        owner = context.get("owner_details", {})

        checks = [
            vehicle.get("make"),
            vehicle.get("model"),
            vehicle.get("year"),
            vehicle.get("mileage"),
            context.get("reason_for_sale"),
            owner.get("email"),
            owner.get("name"),
            context.get("consigner_stage") == "ready_to_list",
        ]

        return all(checks)

    def _create_listing_now(self, context: Dict) -> Dict[str, Any]:
        """CREATE LISTING IN DATABASE"""
        try:
            from consignment_manager import consignment_manager

            vehicle = context.get("vehicle_details", {})
            service = context.get("service_history", {})
            specs = context.get("specifications", {})
            condition = context.get("condition", {})
            owner = context.get("owner_details", {})

            result = consignment_manager.create_listing(
                vehicle_details=vehicle,
                service_history=service,
                specifications=specs,
                condition_assessment=condition,
                asking_price=context.get("asking_price"),
                marketplaces=context.get("marketplaces", []),
                owner_contact=owner,
                valuation=context.get("valuation", {}),
            )

            return result

        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"Error: {str(e)}"}

    def _analyze_intent(self, text: str, context: Dict) -> Dict[str, Any]:
        """Analyze user intent - simplified"""
        text_lower = text.lower()
        stage = context.get("consigner_stage", "")

        # Vehicle make
        makes = [
            "Lamborghini",
            "Ferrari",
            "Porsche",
            "BMW",
            "Mercedes",
            "Audi",
            "McLaren",
        ]
        for make in makes:
            if make.lower() in text_lower:
                return {"type": "vehicle_make"}

        # Model (if we're on model stage)
        if stage == "vehicle_model":
            return {"type": "vehicle_model"}

        # Year
        if re.search(r"(20\d{2})", text):
            return {"type": "vehicle_year"}

        # Color (if on color stage)
        if stage == "vehicle_color":
            return {"type": "vehicle_color"}

        # Mileage
        if (
            re.search(r"(\d+)\s*(?:k|miles|km)", text_lower)
            or stage == "vehicle_mileage"
        ):
            return {"type": "vehicle_mileage"}

        # Reason for sale
        if stage == "reason_for_sale":
            return {"type": "reason_for_sale"}

        # Owner details
        if "@" in text or re.search(r"\+?\d{10,}", text):
            return {"type": "owner_details"}

        return {"type": "general"}

    def _extract_vehicle_make(self, text: str) -> Optional[str]:
        """Extract vehicle make"""
        makes = [
            "Lamborghini",
            "Ferrari",
            "Porsche",
            "BMW",
            "Mercedes",
            "Audi",
            "McLaren",
            "Aston Martin",
        ]
        for make in makes:
            if make.lower() in text.lower():
                return make
        return None

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year"""
        year_match = re.search(r"(20\d{2})", text)
        if year_match:
            return int(year_match.group(1))
        return None

    def _extract_mileage(self, text: str) -> Optional[int]:
        """Extract mileage"""
        # Handle formats like "220 miles", "5k", "5000"
        mileage_match = re.search(r"(\d+)\s*(?:k|miles|km)?", text.lower())
        if mileage_match:
            value = int(mileage_match.group(1))
            # If it's just a number with 'k', multiply by 1000
            if "k" in text.lower():
                value *= 1000
            return value
        return None

    def _calculate_valuation(self, context: Dict) -> Dict:
        """Calculate market valuation"""
        vehicle = context.get("vehicle_details", {})
        mileage = vehicle.get("mileage", 0)
        year = vehicle.get("year", datetime.now().year)

        # Simple valuation formula (in production, use real market data)
        base_value = 200000  # Base value for luxury cars
        age_depreciation = (datetime.now().year - year) * 0.10  # 10% per year
        mileage_depreciation = (mileage / 10000) * 0.03  # 3% per 10k miles

        trade_in = int(
            base_value * (1 - age_depreciation) * (1 - mileage_depreciation) * 0.7
        )
        private_sale = int(trade_in * 1.2)
        retail = int(private_sale * 1.15)

        return {
            "trade_in": trade_in,
            "private_sale": private_sale,
            "retail": retail,
        }

    def _extract_owner_details(self, text: str) -> Dict[str, str]:
        """Extract owner contact details"""
        details = {}

        # Email
        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        if email_match:
            details["email"] = email_match.group(0)

        # Phone
        phone_match = re.search(r"(\+?\d{10,15})", text)
        if phone_match:
            details["phone"] = phone_match.group(0)

        # Name
        text_clean = text
        if email_match:
            text_clean = text_clean.replace(email_match.group(0), "")
        if phone_match:
            text_clean = text_clean.replace(phone_match.group(0), "")

        parts = text_clean.replace(",", " ").split()
        name_candidates = [
            w for w in parts if len(w) > 1 and w.replace(".", "").isalpha()
        ]
        if name_candidates:
            # Take first 2 words as name, capitalize
            name = " ".join(name_candidates[:2])
            details["name"] = " ".join(word.capitalize() for word in name.split())

        return details

    def _check_owner_details(self, details: Dict) -> List[str]:
        """Check missing owner details"""
        missing = []
        if not details.get("name"):
            missing.append("name")
        if not details.get("email"):
            missing.append("email")
        if not details.get("phone"):
            missing.append("phone")
        return missing


# Singleton
phase3_consigner = Phase3Consigner()
