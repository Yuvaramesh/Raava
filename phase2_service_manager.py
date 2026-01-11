"""
Raava AI Service Manager - Phase 2 FIXED
CLEAN separation from Phase 1 - Only uses service-specific data
"""

import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import OPENAI_API_KEY, LLM_MODEL_NAME, LLM_TEMPERATURE
from datetime import datetime, timedelta
import re


class Phase2ServiceManager:
    """
    Raava AI Service Manager - FIXED with clean service context
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=0.6,
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava AI Service Manager - vehicle maintenance and service specialist.

🎯 MISSION: Help customers book service appointments with CLEAN SERVICE-ONLY DATA

💬 CONVERSATION FLOW:

1. **VEHICLE INFO**: Ask make, model, year, mileage
2. **SERVICE REQUEST**: What service do they need?
3. **CUSTOMER DETAILS**: Name, email, phone, postcode
4. **PROVIDER SELECTION**: Show top 3 service centers
5. **DATE SELECTION**: Pick preferred date/time
6. **CONFIRM & BOOK**: Create appointment in Services collection

🔑 CRITICAL APPOINTMENT CREATION RULES:

When you have ALL of these:
✅ Vehicle info (make, model, year, mileage)
✅ Service request details
✅ Customer details (name, email, phone, postcode)
✅ Selected provider
✅ Appointment date confirmed

Then you MUST respond with EXACTLY this format:

"CREATE_APPOINTMENT_NOW

Vehicle: [make model year - mileage miles]
Service: [service type]
Provider: [provider name, location]
Date: [date and time]
Customer: [name, email, phone]"

This triggers the appointment creation system.

NEVER use Phase 1 data like payment_method, finance_type, selected_vehicle!

Always end with: [Replied by: Raava AI Service Manager]"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process with CLEAN service context"""
        messages = state.get("messages", [])
        session_context = state.get("context", {})

        # Get last user message
        last_user_message = ""
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break

        # 🔥 CRITICAL: Initialize ONLY service-related fields
        if not session_context.get("service_stage"):
            session_context = self._initialize_clean_service_context(session_context)

        print(f"\n🔧 SERVICE MANAGER - Stage: {session_context.get('service_stage')}")
        print(f"🔧 User: {last_user_message}")

        # 🔥 Extract ONLY service fields (ignore Phase 1 fields)
        service_context = self._extract_service_context(session_context)

        print(f"🔧 Clean Service Context: {service_context}")

        enhanced_context = ""

        # 🔥 CRITICAL: First check if we're missing providers and should load them
        if service_context.get(
            "service_stage"
        ) == "provider_selection" and not service_context.get("available_providers"):

            # Load providers immediately
            print(
                "⚠️ Stage is provider_selection but no providers loaded - loading now..."
            )
            providers = self._search_service_providers(service_context)
            service_context["available_providers"] = providers
            enhanced_context += "\n\n🔧 SERVICE PROVIDERS:\n"
            enhanced_context += self._format_providers(providers)
            enhanced_context += "\nASK: Which provider? (1, 2, or 3)\n"

        # Also check if we just collected customer info
        if (
            service_context.get("service_stage") == "collecting_customer_info"
            and service_context.get("customer_service_info")
            and not service_context.get("available_providers")
        ):

            missing = self._check_customer_info(
                service_context["customer_service_info"]
            )
            if not missing:
                # We have customer info, move to provider selection
                print("✅ Customer info complete, searching providers...")
                service_context["service_stage"] = "provider_selection"
                providers = self._search_service_providers(service_context)
                service_context["available_providers"] = providers
                enhanced_context += "\n\n✅ CUSTOMER INFO COLLECTED\n"
                enhanced_context += self._format_providers(providers)
                enhanced_context += "\nASK: Which provider? (1, 2, or 3)\n"

        # 🔥 FIRST: Check if we should CREATE APPOINTMENT
        if self._should_create_appointment(service_context):
            print("🔥 CREATING APPOINTMENT NOW!")
            appointment_result = self._create_appointment_now(service_context)

            if appointment_result.get("success"):
                print(
                    f"✅ APPOINTMENT CREATED: {appointment_result.get('appointment_id')}"
                )

                # Update service context
                service_context["appointment_created"] = True
                service_context["appointment_id"] = appointment_result.get(
                    "appointment_id"
                )
                service_context["service_stage"] = "appointment_completed"

                # Save back to session
                self._save_service_context(session_context, service_context)

                return {
                    "messages": [AIMessage(content=appointment_result["message"])],
                    "context": session_context,
                }
            else:
                print(
                    f"❌ APPOINTMENT CREATION FAILED: {appointment_result.get('message')}"
                )
                enhanced_context += (
                    f"\n\n❌ ERROR: {appointment_result.get('message')}\n"
                )

        # 🔥 NEW: Process multiple intents in order
        intents = self._analyze_multi_intent(last_user_message, service_context)
        print(f"🔧 Detected {len(intents)} intent(s): {[i['type'] for i in intents]}")

        for intent in intents:
            print(f"🔧 Processing intent: {intent['type']}")

            # Handle vehicle info
            if intent["type"] == "vehicle_info":
                extracted = self._extract_vehicle_info(last_user_message)
                if not service_context.get("vehicle_info"):
                    service_context["vehicle_info"] = {}
                service_context["vehicle_info"].update(extracted)

                missing = self._check_vehicle_info(service_context["vehicle_info"])
                if not missing:
                    service_context["service_stage"] = "service_request"
                    enhanced_context += "\n\n✅ VEHICLE INFO COLLECTED\n"
                    enhanced_context += "ASK: What service do you need? (e.g., annual service, MOT, brake check)\n"
                else:
                    enhanced_context += f"\n\n📋 Still need: {', '.join(missing)}\n"

            # Handle service request
            elif intent["type"] == "service_request":
                service_context["service_request"] = {
                    "type": intent.get("service_type", "general_service"),
                    "description": last_user_message,
                    "urgency": intent.get("urgency", "routine"),
                }
                service_context["service_stage"] = "collecting_customer_info"
                enhanced_context += "\n\n✅ SERVICE REQUEST NOTED\n"
                enhanced_context += "ASK: Your name, email, phone, and postcode?\n"

            # Handle customer info
            elif intent["type"] == "customer_info":
                extracted = self._extract_customer_service_info(last_user_message)
                if not service_context.get("customer_service_info"):
                    service_context["customer_service_info"] = {}
                service_context["customer_service_info"].update(extracted)

                print(f"📋 Extracted customer info: {extracted}")
                print(
                    f"📋 Current customer info: {service_context['customer_service_info']}"
                )

                missing = self._check_customer_info(
                    service_context["customer_service_info"]
                )
                if not missing:
                    service_context["service_stage"] = "provider_selection"
                    # Trigger provider search
                    providers = self._search_service_providers(service_context)
                    service_context["available_providers"] = providers
                    enhanced_context += "\n\n✅ CUSTOMER INFO COLLECTED\n"
                    enhanced_context += self._format_providers(providers)
                    enhanced_context += "\nASK: Which provider? (1, 2, or 3)\n"
                else:
                    enhanced_context += f"\n\n📋 Still need: {', '.join(missing)}\n"
                    enhanced_context += (
                        f"Current info: {service_context['customer_service_info']}\n"
                    )

            # Handle provider selection
            elif intent["type"] == "provider_selection":
                idx = intent.get("provider_index")

                # 🔥 CRITICAL: Ensure providers are loaded first
                if not service_context.get("available_providers"):
                    print(
                        "⚠️ Trying to select provider but none loaded - loading now..."
                    )
                    providers = self._search_service_providers(service_context)
                    service_context["available_providers"] = providers
                    enhanced_context += "\n\n🔧 SERVICE PROVIDERS:\n"
                    enhanced_context += self._format_providers(providers)

                providers = service_context.get("available_providers", [])
                if idx is not None and providers:
                    if 0 <= idx < len(providers):
                        service_context["selected_provider"] = providers[idx]
                        service_context["service_stage"] = "date_selection"
                        enhanced_context += (
                            f"\n\n✅ PROVIDER SELECTED: {providers[idx]['name']}\n"
                        )
                        enhanced_context += "ASK: Preferred date and time? (e.g., 'Tomorrow 2pm' or 'Next Monday 10am' or '2026-01-15 11:00 AM')\n"
                    else:
                        enhanced_context += (
                            f"\n\n❌ Invalid selection. Please choose 1, 2, or 3\n"
                        )
                else:
                    enhanced_context += f"\n\n❌ No providers available. Please provide customer info first.\n"

            # Handle date selection
            elif intent["type"] == "date_selection":
                date_info = self._parse_appointment_date(last_user_message)
                if date_info:
                    service_context["appointment_date"] = date_info
                    service_context["service_stage"] = "ready_to_book"
                    enhanced_context += (
                        f"\n\n✅ DATE SELECTED: {date_info['formatted']}\n"
                    )
                    enhanced_context += "ASK: Confirm booking? (Yes/No)\n"

            # Handle confirmation
            elif intent["type"] == "confirmation":
                if intent.get("confirmed"):
                    service_context["service_stage"] = "ready_to_book"
                    enhanced_context += (
                        "\n\n✅ CONFIRMED - READY TO CREATE APPOINTMENT\n"
                    )
                else:
                    enhanced_context += (
                        "\n\n❌ Not confirmed. What would you like to change?\n"
                    )

        # Save service context back
        self._save_service_context(session_context, service_context)

        # Build conversation
        conversation_messages = [
            SystemMessage(content=self.system_prompt + enhanced_context)
        ]

        for msg in messages[-6:]:
            conversation_messages.append(msg)

        # Get response
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

        # 🔥 Check if LLM said to create appointment
        if "CREATE_APPOINTMENT_NOW" in response_text:
            print("🔥 LLM TRIGGERED APPOINTMENT CREATION")
            appointment_result = self._create_appointment_now(service_context)

            if appointment_result.get("success"):
                response_text = appointment_result["message"]
                service_context["appointment_created"] = True
                service_context["appointment_id"] = appointment_result.get(
                    "appointment_id"
                )
                self._save_service_context(session_context, service_context)

        print(
            f"✅ Service Manager returning - Stage: {service_context.get('service_stage')}"
        )

        return {
            "messages": [AIMessage(content=response_text)],
            "context": session_context,
        }

    def _initialize_clean_service_context(self, context: Dict) -> Dict:
        """Initialize ONLY service fields"""
        # Preserve session tracking
        service_fields = {
            "session_id": context.get("session_id"),
            "routed": context.get("routed", True),
            "active_agent": "phase2_service_manager",
            # ONLY service-specific fields
            "service_stage": "vehicle_info",
            "vehicle_info": {},
            "service_request": {},
            "customer_service_info": {},
            "available_providers": [],
            "selected_provider": None,
            "appointment_date": None,
            "appointment_created": False,
            "appointment_id": None,
        }
        return service_fields

    def _extract_service_context(self, context: Dict) -> Dict:
        """Extract ONLY service-related fields"""
        return {
            "session_id": context.get("session_id"),
            "service_stage": context.get("service_stage", "vehicle_info"),
            "vehicle_info": context.get("vehicle_info", {}),
            "service_request": context.get("service_request", {}),
            "customer_service_info": context.get("customer_service_info", {}),
            "available_providers": context.get("available_providers", []),
            "selected_provider": context.get("selected_provider"),
            "appointment_date": context.get("appointment_date"),
            "appointment_created": context.get("appointment_created", False),
            "appointment_id": context.get("appointment_id"),
        }

    def _save_service_context(self, session_context: Dict, service_context: Dict):
        """Save service context back to session"""
        session_context.update(service_context)

    def _should_create_appointment(self, context: Dict) -> bool:
        """Check if we have everything needed for appointment - STRICT validation"""
        vehicle = context.get("vehicle_info", {})
        service = context.get("service_request", {})
        customer = context.get("customer_service_info", {})
        provider = context.get("selected_provider")
        date = context.get("appointment_date")

        print("\n🔍 APPOINTMENT READINESS CHECK:")

        # Check vehicle info
        vehicle_ok = all(
            [
                vehicle.get("make"),
                vehicle.get("model"),
            ]
        )
        print(
            f"   Vehicle: {'✅' if vehicle_ok else '❌'} (make={vehicle.get('make')}, model={vehicle.get('model')})"
        )

        # Check service request
        service_ok = service.get("type") is not None
        print(
            f"   Service: {'✅' if service_ok else '❌'} (type={service.get('type')})"
        )

        # Check customer info
        customer_ok = all(
            [
                customer.get("email"),
                customer.get("name"),
            ]
        )
        print(
            f"   Customer: {'✅' if customer_ok else '❌'} (email={customer.get('email')}, name={customer.get('name')})"
        )

        # Check provider
        provider_ok = provider is not None
        print(
            f"   Provider: {'✅' if provider_ok else '❌'} ({provider.get('name') if provider else 'None'})"
        )

        # Check date
        date_ok = date is not None
        print(
            f"   Date: {'✅' if date_ok else '❌'} ({date.get('formatted') if date else 'None'})"
        )

        # Stage must be ready
        stage_ok = context.get("service_stage") == "ready_to_book"
        print(
            f"   Stage: {'✅' if stage_ok else '❌'} ({context.get('service_stage')})"
        )

        # ALL must be true
        all_ok = all(
            [vehicle_ok, service_ok, customer_ok, provider_ok, date_ok, stage_ok]
        )

        if all_ok:
            print("   ✅ ALL REQUIREMENTS MET FOR APPOINTMENT CREATION")
        else:
            print("   ❌ MISSING REQUIRED DATA - CANNOT CREATE APPOINTMENT")

        return all_ok

    def _create_appointment_now(self, context: Dict) -> Dict[str, Any]:
        """CREATE APPOINTMENT IN SERVICES COLLECTION"""
        try:
            from service_booking_manager import service_booking_manager

            vehicle = context.get("vehicle_info", {})
            service = context.get("service_request", {})
            customer = context.get("customer_service_info", {})
            provider = context.get("selected_provider", {})
            date = context.get("appointment_date", {})

            print(f"\n🔥 CREATING SERVICE APPOINTMENT:")
            print(f"   Vehicle: {vehicle.get('make')} {vehicle.get('model')}")
            print(f"   Service: {service.get('type')}")
            print(f"   Customer: {customer.get('email')}")
            print(f"   Provider: {provider.get('name')}")

            # CREATE APPOINTMENT
            result = service_booking_manager.create_service_appointment(
                vehicle_info=vehicle,
                service_request=service,
                customer_info=customer,
                provider_info=provider,
                appointment_datetime=date.get("datetime"),
            )

            if result.get("success"):
                print(f"✅ APPOINTMENT CREATED: {result.get('appointment_id')}")
                return result
            else:
                print(f"❌ FAILED: {result.get('message')}")
                return result

        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"Error: {str(e)}"}

    def _analyze_multi_intent(self, text: str, context: Dict) -> List[Dict[str, Any]]:
        """Analyze and detect MULTIPLE intents in one message - processes in order"""
        text_lower = text.lower()
        stage = context.get("service_stage", "")
        intents = []

        print(f"🔍 Multi-intent analysis - Stage: {stage}, Text: {text}")

        # 🔥 Detect all possible intents in order of priority

        # 1. Provider selection (if stage is provider_selection OR if we have providers)
        # Check for single digit 1-3 in the message
        if stage == "provider_selection" or context.get("available_providers"):
            # Look for standalone number 1-3
            match = re.search(r"^([1-3])$", text.strip())
            if match:
                print(f"   ✅ Found provider selection: {match.group(1)}")
                intents.append(
                    {
                        "type": "provider_selection",
                        "provider_index": int(match.group(1)) - 1,
                    }
                )

        # 2. Date selection
        if (
            re.search(r"\d{4}-\d{2}-\d{2}", text)  # 2026-01-13
            or re.search(r"\d{2}/\d{2}/\d{4}", text)  # 13/01/2026
            or re.search(r"\d{1,2}[:.]\d{2}", text)  # 11:30 or 11.30
            or any(
                w in text_lower
                for w in [
                    "tomorrow",
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                    "next week",
                    "am",
                    "pm",
                ]
            )
        ):
            print("   ✅ Found date selection")
            intents.append({"type": "date_selection"})

        # 3. Confirmation (only if in ready_to_book stage)
        if stage == "ready_to_book":
            if any(
                w in text_lower
                for w in ["yes", "confirm", "ok", "sure", "book", "proceed"]
            ):
                print("   ✅ Found confirmation: YES")
                intents.append({"type": "confirmation", "confirmed": True})
            elif any(w in text_lower for w in ["no", "cancel", "wait", "change"]):
                print("   ❌ Found confirmation: NO")
                intents.append({"type": "confirmation", "confirmed": False})

        # 4. Customer info (email/phone)
        if "@" in text or re.search(r"\+?\d{10,}", text):
            print("   ✅ Found customer info (email/phone)")
            intents.append({"type": "customer_info"})

        # 5. Vehicle info
        if any(
            w in text_lower
            for w in [
                "lamborghini",
                "ferrari",
                "porsche",
                "bmw",
                "mercedes",
                "audi",
                "mclaren",
            ]
        ):
            print("   ✅ Found vehicle info (make mentioned)")
            intents.append({"type": "vehicle_info"})

        # 6. Service request
        if any(
            w in text_lower
            for w in [
                "service",
                "mot",
                "repair",
                "check",
                "maintenance",
                "oil",
                "brake",
                "miles",
            ]
        ):
            print("   ✅ Found service request")
            intents.append(
                {
                    "type": "service_request",
                    "service_type": "scheduled_service",
                    "urgency": "routine",
                }
            )

        # If no intents found, return general
        if not intents:
            print("   ⚠️ No specific intents - returning general")
            intents.append({"type": "general"})

        return intents

    def _analyze_intent(self, text: str, context: Dict) -> Dict[str, Any]:
        """Single intent analysis - DEPRECATED, use _analyze_multi_intent instead"""
        # This is kept for backward compatibility but should use multi-intent
        intents = self._analyze_multi_intent(text, context)
        return intents[0] if intents else {"type": "general"}

    def _extract_vehicle_info(self, text: str) -> Dict[str, str]:
        """Extract vehicle info"""
        info = {}
        text_lower = text.lower()

        # Make
        makes = [
            "lamborghini",
            "ferrari",
            "porsche",
            "bmw",
            "mercedes",
            "audi",
            "mclaren",
        ]
        for make in makes:
            if make in text_lower:
                info["make"] = make.title()
                break

        # Model
        words = text.split()
        if info.get("make"):
            make_idx = next(
                (i for i, w in enumerate(words) if w.lower() == info["make"].lower()),
                -1,
            )
            if make_idx >= 0 and make_idx + 1 < len(words):
                info["model"] = " ".join(words[make_idx + 1 : make_idx + 3])

        # Year
        year_match = re.search(r"(20\d{2})", text)
        if year_match:
            info["year"] = int(year_match.group(1))

        # Mileage
        mileage_match = re.search(r"(\d+)\s*(?:k|miles)", text_lower)
        if mileage_match:
            info["mileage"] = int(mileage_match.group(1))

        return info

    def _check_vehicle_info(self, vehicle: Dict) -> List[str]:
        """Check missing vehicle info"""
        missing = []
        if not vehicle.get("make"):
            missing.append("make")
        if not vehicle.get("model"):
            missing.append("model")
        if not vehicle.get("year"):
            missing.append("year")
        if not vehicle.get("mileage"):
            missing.append("mileage")
        return missing

    def _extract_customer_service_info(self, text: str) -> Dict[str, str]:
        """Extract customer service info - FIXED"""
        info = {}

        print(f"📧 Extracting customer info from: {text}")

        # Email
        email = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        if email:
            info["email"] = email.group(0)
            print(f"   ✅ Email: {info['email']}")

        # Phone - improved pattern for international numbers
        phone = re.search(r"(\+?\d{10,15})", text)
        if phone:
            info["phone"] = phone.group(0)
            print(f"   ✅ Phone: {info['phone']}")

        # Postcode (UK format) - more flexible pattern
        postcode = re.search(
            r"\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b", text, re.IGNORECASE
        )
        if postcode:
            info["postcode"] = postcode.group(0).upper()
            print(f"   ✅ Postcode: {info['postcode']}")

        # Name - extract from what's left after removing email, phone, postcode
        text_clean = text
        if email:
            text_clean = text_clean.replace(email.group(0), "")
        if phone:
            text_clean = text_clean.replace(phone.group(0), "")
        if postcode:
            text_clean = text_clean.replace(postcode.group(0), "")

        # Remove common words and separators
        text_clean = re.sub(r"[,;]", " ", text_clean)
        parts = text_clean.split()

        # Filter out non-name words
        name_candidates = []
        for word in parts:
            word = word.strip()
            # Skip if it's too short, has numbers, or is a common word
            if (
                len(word) > 1
                and word.replace(".", "").isalpha()
                and word.lower()
                not in [
                    "my",
                    "name",
                    "is",
                    "email",
                    "phone",
                    "postcode",
                    "and",
                    "the",
                    "at",
                ]
            ):
                name_candidates.append(word)

        if name_candidates:
            # Take first 1-2 words as name
            info["name"] = " ".join(name_candidates[:2]).title()
            print(f"   ✅ Name: {info['name']}")

        print(f"   📊 Total extracted: {info}")
        return info

    def _check_customer_info(self, customer: Dict) -> List[str]:
        """Check missing customer info"""
        missing = []
        if not customer.get("name"):
            missing.append("name")
        if not customer.get("email"):
            missing.append("email")
        if not customer.get("phone"):
            missing.append("phone")
        if not customer.get("postcode"):
            missing.append("postcode")
        return missing

    def _search_service_providers(self, context: Dict) -> List[Dict]:
        """Search service providers (mock for now)"""
        # In production, would use real provider search
        return [
            {
                "name": "Autoshield",
                "location": "Cuffley, Hertfordshire",
                "distance_miles": 15.6,
                "rating": 4.9,
                "specialties": ["Lamborghini specialist"],
                "phone": "01707 888890",
                "estimated_cost": 325,
            },
            {
                "name": "Performance Direct",
                "location": "London",
                "distance_miles": 20.2,
                "rating": 4.8,
                "specialties": ["Exotic cars"],
                "phone": "020 1234 5678",
                "estimated_cost": 450,
            },
            {
                "name": "Elite Motors",
                "location": "Manchester",
                "distance_miles": 180.5,
                "rating": 4.7,
                "specialties": ["Luxury service"],
                "phone": "0161 123 4567",
                "estimated_cost": 375,
            },
        ]

    def _format_providers(self, providers: List[Dict]) -> str:
        """Format providers"""
        result = "\n\n🔧 SERVICE PROVIDERS:\n\n"
        for i, p in enumerate(providers, 1):
            result += f"{i}. **{p['name']}** ({p['location']})\n"
            result += f"   • {p['distance_miles']} miles away\n"
            result += f"   • Rating: {p['rating']}⭐\n"
            result += f"   • Est. Cost: £{p['estimated_cost']}\n\n"
        return result

    def _parse_appointment_date(self, text: str) -> Optional[Dict]:
        """Parse appointment date - FIXED to handle multiple formats"""
        text_lower = text.lower()
        now = datetime.now()

        print(f"🗓️ Parsing date from: {text}")

        # Try to extract date and time
        date = None
        hour = 10  # default hour
        minute = 0  # default minute

        # Format 1: YYYY-MM-DD
        date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if date_match:
            year, month, day = map(int, date_match.groups())
            date = datetime(year, month, day)
            print(f"   📅 Extracted date: {date.date()}")

        # Format 2: DD/MM/YYYY
        if not date:
            date_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
            if date_match:
                day, month, year = map(int, date_match.groups())
                date = datetime(year, month, day)
                print(f"   📅 Extracted date: {date.date()}")

        # Format 3: Relative dates
        if not date:
            if "tomorrow" in text_lower:
                date = now + timedelta(days=1)
                print(f"   📅 Tomorrow: {date.date()}")
            elif "next week" in text_lower or "monday" in text_lower:
                days_ahead = 7 - now.weekday()
                date = now + timedelta(days=days_ahead)
                print(f"   📅 Next Monday: {date.date()}")
            elif "tuesday" in text_lower:
                days_ahead = (1 - now.weekday()) % 7
                date = now + timedelta(days=days_ahead if days_ahead > 0 else 7)
                print(f"   📅 Tuesday: {date.date()}")
            else:
                # Default to tomorrow
                date = now + timedelta(days=1)
                print(f"   📅 Default (tomorrow): {date.date()}")

        # Extract time
        # Format: HH.MM or HH:MM or HH.MM am/pm
        time_match = re.search(r"(\d{1,2})[.:](\d{2})", text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))

            # Handle AM/PM
            if "pm" in text_lower and hour < 12:
                hour += 12
            elif "am" in text_lower and hour == 12:
                hour = 0

            print(f"   🕐 Extracted time: {hour:02d}:{minute:02d}")
        else:
            # Try to extract just hour
            hour_match = re.search(r"(\d{1,2})\s*(?:am|pm)", text_lower)
            if hour_match:
                hour = int(hour_match.group(1))
                if "pm" in text_lower and hour < 12:
                    hour += 12
                elif "am" in text_lower and hour == 12:
                    hour = 0
                print(f"   🕐 Extracted hour: {hour:02d}:00")

        # Combine date and time
        if date:
            date = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            formatted = date.strftime("%A, %d %B %Y at %I:%M %p")
            print(f"   ✅ Final datetime: {formatted}")

            return {
                "datetime": date,
                "formatted": formatted,
            }

        print("   ❌ Could not parse date")
        return None


# Singleton
phase2_service_manager = Phase2ServiceManager()
