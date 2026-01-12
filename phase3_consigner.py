"""
Raava AI Consigner - Phase 3 SIMPLIFIED
Help users sell their vehicles with minimal questions - NO LOOPS
Only asks: Make, Model, Year, Color, Mileage, Reason for Sale, Owner Details (Name, Email, Phone)
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
    Raava AI Consigner - Vehicle selling specialist (SIMPLIFIED - NO LOOPS)
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava AI Consigner - professional vehicle listing specialist.

🎯 MISSION: Help customers sell their vehicles with professional listings

📋 STRICT CONVERSATION FLOW - Ask ONLY these questions in THIS ORDER:

1. **VEHICLE MAKE**: What make is your car? (e.g., Lamborghini, Ferrari, Porsche)
2. **MODEL**: What model? (e.g., Huracan Evo, 488 GTB, 911 Turbo)
3. **YEAR**: What year?
4. **COLOR**: What color is the car?
5. **MILEAGE**: Current mileage?
6. **REASON FOR SALE**: Why are you selling?
7. **OWNER DETAILS**: Please provide your full name, email, and phone number

🚫 DO NOT:
- Ask the same question twice
- Ask questions out of order
- Ask about: service history, specs, photos, condition details, marketplaces, valuation
- Loop back to previous questions

✅ USE DEFAULTS FOR:
- Service History: "Available on request"
- Specifications: Standard manufacturer specs
- Photos: "Professional photography available"
- Condition: "Excellent condition throughout"
- Asking Price: Calculate based on make/model/year/mileage

🎯 WHEN ALL DATA IS COLLECTED:
Summarize: "Great! I have all your details. Your {year} {make} {model} ({color}, {mileage} miles) is ready to list for £{price}. Listing created!"

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

        # Extract data for CURRENT stage only
        if consigner_context.get("consigner_stage") == "vehicle_make":
            extracted = self._extract_vehicle_make(last_user_message)
            if extracted:
                consigner_context["vehicle_details"]["make"] = extracted
                consigner_context["consigner_stage"] = "vehicle_model"

        elif consigner_context.get("consigner_stage") == "vehicle_model":
            model = last_user_message.strip()
            if model and len(model) > 1:  # Validate not empty
                consigner_context["vehicle_details"]["model"] = model
                consigner_context["consigner_stage"] = "vehicle_year"

        elif consigner_context.get("consigner_stage") == "vehicle_year":
            year = self._extract_year(last_user_message)
            if year:
                consigner_context["vehicle_details"]["year"] = year
                consigner_context["consigner_stage"] = "vehicle_color"

        elif consigner_context.get("consigner_stage") == "vehicle_color":
            color = last_user_message.strip()
            if color and len(color) > 1:  # Validate not empty
                consigner_context["vehicle_details"]["color"] = color
                consigner_context["consigner_stage"] = "vehicle_mileage"

        elif consigner_context.get("consigner_stage") == "vehicle_mileage":
            mileage = self._extract_mileage(last_user_message)
            if mileage:
                consigner_context["vehicle_details"]["mileage"] = mileage
                consigner_context["consigner_stage"] = "reason_for_sale"

        elif consigner_context.get("consigner_stage") == "reason_for_sale":
            reason = last_user_message.strip()
            if reason and len(reason) > 3:  # Validate minimum length
                consigner_context["reason_for_sale"] = reason
                # Calculate valuation after reason is collected
                valuation = self._calculate_valuation(consigner_context)
                consigner_context["valuation"] = valuation
                consigner_context["asking_price"] = valuation.get("private_sale", 0)
                consigner_context["consigner_stage"] = "owner_details"

        elif consigner_context.get("consigner_stage") == "owner_details":
            owner_info = self._extract_owner_details(last_user_message)
            existing_owner = consigner_context.get("owner_details", {})
            existing_owner.update(owner_info)
            consigner_context["owner_details"] = existing_owner

            missing = self._check_owner_details(existing_owner)
            if not missing:
                consigner_context["consigner_stage"] = "ready_to_list"

        # Save context
        self._save_consigner_context(session_context, consigner_context)

        # Check if ready to create listing
        if consigner_context.get(
            "consigner_stage"
        ) == "ready_to_list" and not consigner_context.get("listing_created"):
            print("🔥 CREATING LISTING NOW!")
            listing_result = self._create_listing_now(consigner_context)

            if listing_result.get("success"):
                consigner_context["listing_created"] = True
                consigner_context["listing_id"] = listing_result.get("listing_id")
                self._save_consigner_context(session_context, consigner_context)

                return {
                    "messages": [AIMessage(content=listing_result["message"])],
                    "context": session_context,
                }

        # Build LLM conversation for response only
        conversation_messages = [SystemMessage(content=self.system_prompt)]

        # Add last 2 messages for context (don't send full history)
        for msg in messages[-2:]:
            conversation_messages.append(msg)

        # Get response from LLM
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

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
            "service_history": {
                "description": "Available on request",
                "full_history": True,
            },
            "specifications": {"description": "Standard manufacturer specifications"},
            "condition": {"rating": 9, "notes": "Excellent condition throughout"},
            "photos_ready": True,
            "marketplaces": ["AutoTrader"],
            "asking_price": 0,
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
            "Jaguar",
            "Range Rover",
            "Bentley",
            "Rolls Royce",
        ]
        for make in makes:
            if make.lower() in text.lower():
                return make
        return None

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text"""
        year_match = re.search(r"(19\d{2}|20\d{2})", text)
        if year_match:
            year = int(year_match.group(1))
            current_year = datetime.now().year
            # Validate it's a reasonable year (1970 to current year)
            if 1970 <= year <= current_year:
                return year
        return None

    def _extract_mileage(self, text: str) -> Optional[int]:
        """Extract mileage from text"""
        # Handle formats like "220 miles", "5k", "5000"
        mileage_match = re.search(r"(\d+)\s*(?:k|miles|km)?", text.lower())
        if mileage_match:
            value = int(mileage_match.group(1))
            if "k" in text.lower():
                value *= 1000
            # Validate reasonable mileage
            if 0 <= value <= 500000:
                return value
        return None

    def _calculate_valuation(self, context: Dict) -> Dict:
        """Calculate market valuation"""
        vehicle = context.get("vehicle_details", {})
        mileage = vehicle.get("mileage", 0)
        year = vehicle.get("year", datetime.now().year)

        # Simple valuation formula (in production, use real market data)
        base_value = 200000
        age_depreciation = (datetime.now().year - year) * 0.10
        mileage_depreciation = (mileage / 10000) * 0.03

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
        """Extract owner contact details from text"""
        details = {}

        # Email pattern
        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        if email_match:
            details["email"] = email_match.group(0)

        # Phone pattern - improved for international formats
        phone_match = re.search(r"(\+?\d{1,3}[\s\-]?\d{3,4}[\s\-]?\d{3,4})", text)
        if phone_match:
            details["phone"] = phone_match.group(0).strip()

        # Name extraction
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
