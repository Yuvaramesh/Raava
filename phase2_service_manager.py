"""
Raava AI Service Manager - Phase 2 (FIXED - Properly returns appointment_created flag)
"""

import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from datetime import datetime, timedelta
from config import OPENAI_API_KEY, LLM_MODEL_NAME
from database import db
from service_scheduler import service_scheduler
from service_providers import service_provider_aggregator
import re


class Phase2ServiceManager:
    """Raava AI Service Manager - FIXED to properly return appointment status"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=0.6,
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava AI Service Manager.

Your job: Help customers book service appointments.

Flow:
1. Get vehicle info (make, model, year)
2. Understand service needed
3. Get mileage
4. Get postcode
5. Show 3 providers, get selection
6. Show 5 dates, get selection
7. Get customer details (name, phone, email)
8. CONFIRM appointment with all details

Once you have ALL information and user confirms, say:
"APPOINTMENT BOOKED"

Always end: [Replied by: Raava AI Service Manager]"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process service request - FIXED to return appointment_created properly"""
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
        if not session_context.get("service_stage"):
            session_context["service_stage"] = "vehicle_identification"
            session_context["vehicle_info"] = {}
            session_context["service_request"] = {}
            session_context["customer_service_info"] = {}

        print(f"\n🔧 SERVICE MANAGER - Stage: {session_context.get('service_stage')}")
        print(f"📝 User: {last_user_message[:100]}")

        self._extract_appointment_from_history(messages, session_context)

        if self._is_user_confirming(last_user_message, session_context):
            print("✅ USER CONFIRMED - Starting full confirmation flow...")
            print("=" * 70)

            # STEP 1: Validate all data
            validation = self._validate_appointment_data(session_context)
            if not validation["valid"]:
                print(f"❌ VALIDATION FAILED: {validation['errors']}")
                return {
                    "messages": [
                        AIMessage(
                            content=f"Validation error: {', '.join(validation['errors'])}"
                        )
                    ],
                    "context": session_context,
                }
            print("✅ STEP 1: All data validated successfully")

            # STEP 2: Save appointment to database
            print("\n💾 STEP 2: Saving appointment to database...")
            appointment_result = self._create_service_appointment(session_context)

            if not appointment_result.get("success"):
                print(f"❌ DATABASE SAVE FAILED: {appointment_result.get('message')}")
                return {
                    "messages": [
                        AIMessage(
                            content=f"Error saving appointment: {appointment_result.get('message', 'Unknown error')}"
                        )
                    ],
                    "context": session_context,
                }

            appointment_id = appointment_result.get("appointment_id")
            print(f"✅ STEP 2: Appointment saved to database - ID: {appointment_id}")

            # STEP 3: Email sent (already handled in create_appointment)
            email_status = appointment_result.get("email_sent", False)
            if email_status:
                print(
                    f"✅ STEP 3: Confirmation email sent to {session_context['customer_service_info'].get('email')}"
                )
            else:
                print(
                    f"⚠️ STEP 3: Email sending reported as false - check SMTP configuration"
                )

            # STEP 4: Clear session for fresh conversation
            print(f"\n🧹 STEP 4: Clearing session for fresh conversation...")
            cleared_context = self._clear_session_context(
                session_context, appointment_id
            )
            print(f"✅ STEP 4: Session cleared - all service data reset")
            print("=" * 70)

            # FINAL: Update context and return confirmation
            cleared_context["appointment_created"] = True
            cleared_context["appointment_id"] = appointment_id

            return {
                "messages": [AIMessage(content=appointment_result["message"])],
                "context": cleared_context,
            }

        # Extract information from user message
        self._extract_and_update_context(last_user_message, session_context)

        # Check if we should show providers
        if self._should_show_providers(session_context):
            providers = self._find_providers(session_context)
            if providers:
                session_context["available_providers"] = providers
                session_context["service_stage"] = "provider_selection"

        # Check if provider was selected
        if self._check_provider_selection(last_user_message, session_context):
            provider_idx = self._extract_provider_selection(last_user_message)
            if provider_idx is not None and session_context.get("available_providers"):
                providers = session_context["available_providers"]
                if 0 <= provider_idx < len(providers):
                    selected = providers[provider_idx]
                    session_context["selected_provider"] = selected
                    session_context["service_stage"] = "date_selection"

                    # Generate available slots
                    slots = self._get_available_slots(
                        selected, session_context.get("service_request", {})
                    )
                    session_context["available_slots"] = slots

        # Build context for LLM
        enhanced_context = self._build_enhanced_context(session_context)

        # Build conversation
        conversation_messages = [
            SystemMessage(content=self.system_prompt + enhanced_context)
        ]

        for msg in messages[-6:]:
            conversation_messages.append(msg)

        # Get response
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

        # Return with updated context
        return {
            "messages": [AIMessage(content=response_text)],
            "context": session_context,
        }

    def _is_user_confirming(self, text: str, context: Dict) -> bool:
        """Check if user is confirming the appointment"""
        # Check if user said CONFIRM, yes, or similar
        text_lower = text.strip().lower()

        # Must have all required information
        vehicle = context.get("vehicle_info", {})
        service = context.get("service_request", {})
        provider = context.get("selected_provider")
        date_info = context.get("appointment_date")
        customer = context.get("customer_service_info", {})

        has_all_info = (
            vehicle.get("make")
            and service.get("type")
            and provider
            and date_info
            and customer.get("name")
            and customer.get("email")
            and customer.get("phone")
        )

        if not has_all_info:
            return False

        # Check for confirmation keywords
        confirm_keywords = [
            "confirm",
            "yes",
            "okay",
            "ok",
            "let's",
            "lets",
            "book",
            "proceed",
            "ready",
            "go",
        ]
        return any(keyword in text_lower for keyword in confirm_keywords)

    def _check_if_date_selected(self, text: str, context: Dict) -> bool:
        """Check if user just selected a date"""
        # Must be in date_selection stage
        if context.get("service_stage") != "date_selection":
            return False

        # Must have available slots
        if not context.get("available_slots"):
            return False

        # Must have customer info
        customer = context.get("customer_service_info", {})
        if not all(
            [customer.get("name"), customer.get("email"), customer.get("phone")]
        ):
            return False

        # Check if message is a number 1-5
        text_clean = text.strip().lower()
        if re.match(r"^[1-5]$", text_clean):
            return True

        # Check for "option X" or "slot X"
        if re.search(r"(option|slot|choice|number)\s*[1-5]", text_clean):
            return True

        return False

    def _extract_date_selection(self, text: str, context: Dict) -> Optional[Dict]:
        """Extract which date was selected"""
        slots = context.get("available_slots", [])
        if not slots:
            return None

        # Extract number
        match = re.search(r"(\d)", text.strip())
        if match:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(slots):
                selected_slot = slots[idx]
                print(f"📅 Selected date: {selected_slot.get('display')}")
                return selected_slot

        return None

    def _should_show_providers(self, context: Dict) -> bool:
        """Check if we should search for providers"""
        # Need vehicle info
        vehicle = context.get("vehicle_info", {})
        if not vehicle.get("make"):
            return False

        # Need service type
        if not context.get("service_request", {}).get("type"):
            return False

        # Need postcode
        if not context.get("customer_service_info", {}).get("postcode"):
            return False

        # Haven't shown providers yet
        if context.get("available_providers"):
            return False

        # Not already selected
        if context.get("selected_provider"):
            return False

        return True

    def _check_provider_selection(self, text: str, context: Dict) -> bool:
        """Check if user selected a provider"""
        if context.get("service_stage") != "provider_selection":
            return False

        if not context.get("available_providers"):
            return False

        # Check for number 1-3
        if re.match(r"^[1-3]$", text.strip()):
            return True

        return False

    def _extract_provider_selection(self, text: str) -> Optional[int]:
        """Extract provider selection"""
        match = re.search(r"(\d)", text.strip())
        if match:
            return int(match.group(1)) - 1
        return None

    def _find_providers(self, context: Dict) -> List[Dict]:
        """Find service providers"""
        vehicle = context.get("vehicle_info", {})
        service_req = context.get("service_request", {})
        customer = context.get("customer_service_info", {})

        providers = service_provider_aggregator.find_providers(
            make=vehicle.get("make", ""),
            service_type=service_req.get("type", ""),
            postcode=customer.get("postcode", ""),
            radius_miles=25,
        )

        return providers[:3]

    def _extract_and_update_context(self, text: str, context: Dict):
        """Extract information from user message"""
        text_lower = text.lower()

        # Extract vehicle info
        vehicle_info = self._extract_vehicle_info(text)
        if vehicle_info:
            context["vehicle_info"].update(vehicle_info)

        # Extract mileage
        if not context["vehicle_info"].get("mileage"):
            mileage_match = re.search(r"(\d{1,3}(?:,\d{3})*|\d+)", text_lower)
            if mileage_match:
                mileage_str = mileage_match.group(1).replace(",", "")
                if len(mileage_str) <= 6:  # Reasonable mileage
                    context["vehicle_info"]["mileage"] = int(mileage_str)

        if not context["customer_service_info"].get("postcode"):
            postcode_match = re.search(
                r"\b([A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2})\b", text.upper()
            )
            if postcode_match:
                context["customer_service_info"]["postcode"] = postcode_match.group(1)

        # Extract customer details
        customer_details = self._extract_customer_details(text)
        if customer_details:
            context["customer_service_info"].update(customer_details)

        # Detect service type
        if not context["service_request"].get("type"):
            service_type = self._detect_service_type(text_lower)
            if service_type:
                context["service_request"]["type"] = service_type["type"]
                context["service_request"]["description"] = text
                context["service_request"]["urgency"] = service_type.get(
                    "urgency", "routine"
                )

    def _extract_vehicle_info(self, text: str) -> Dict[str, Any]:
        """Extract vehicle information"""
        info = {}

        car_makes = [
            "Ferrari",
            "Lamborghini",
            "Porsche",
            "McLaren",
            "Aston Martin",
            "Bentley",
            "Rolls-Royce",
            "Mercedes",
            "BMW",
            "Audi",
            "Jaguar",
        ]
        for make in car_makes:
            if make.lower() in text.lower():
                info["make"] = make
                break

        year_match = re.search(r"\b(19|20)(\d{2})\b", text)
        if year_match:
            info["year"] = int(year_match.group(0))

        if info.get("make"):
            pattern = f"{info['make']}\\s+(\\w+(?:\\s+\\w+)?)"
            model_match = re.search(pattern, text, re.IGNORECASE)
            if model_match:
                info["model"] = model_match.group(1).strip()

        return info

    def _extract_customer_details(self, text: str) -> Dict[str, str]:
        """Extract customer details"""
        details = {}

        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        if email_match:
            details["email"] = email_match.group(0)

        phone_match = re.search(r"(\+?\d{10,15})", text)
        if phone_match:
            details["phone"] = phone_match.group(0)

        # Extract name
        text_for_name = text
        if email_match:
            text_for_name = text_for_name.replace(email_match.group(0), "")
        if phone_match:
            text_for_name = text_for_name.replace(phone_match.group(0), "")

        parts = text_for_name.replace(",", " ").split()
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
            details["name"] = " ".join(word.capitalize() for word in name.split())

        return details

    def _detect_service_type(self, text_lower: str) -> Optional[Dict[str, str]]:
        """Detect service type"""
        if any(
            word in text_lower for word in ["brake", "grinding", "noise", "warning"]
        ):
            return {"type": "repair", "urgency": "urgent"}

        if any(word in text_lower for word in ["service", "annual", "maintenance"]):
            return {"type": "scheduled_service", "urgency": "routine"}

        if any(word in text_lower for word in ["upgrade", "enhance", "improve"]):
            return {"type": "upgrade", "urgency": "routine"}

        return None

    def _get_available_slots(self, provider: Dict, service_request: Dict) -> List[Dict]:
        """Get available slots"""
        slots = []
        today = datetime.now()

        for i in range(5):
            days_ahead = i + 1
            slot_date = today + timedelta(days=days_ahead)

            if slot_date.weekday() >= 5:
                days_ahead += 2
                slot_date = today + timedelta(days=days_ahead)

            slots.append(
                {
                    "display": slot_date.strftime("%b %d, %Y at %H:%M").replace(
                        slot_date.strftime("%H"), str(9 + i * 2)
                    ),
                    "date": slot_date.strftime("%Y-%m-%d"),
                    "time": f"{9 + (i * 2):02d}:{'00' if i % 2 == 0 else '30'}",
                }
            )

        return slots

    def _build_enhanced_context(self, context: Dict) -> str:
        """Build context summary for LLM"""
        parts = ["\n\n📋 CURRENT STATUS:"]

        vehicle = context.get("vehicle_info", {})
        if vehicle.get("make"):
            parts.append(
                f"✅ Vehicle: {vehicle.get('make')} {vehicle.get('model', '')} ({vehicle.get('year', '')})"
            )
            if vehicle.get("mileage"):
                parts.append(f"✅ Mileage: {vehicle['mileage']:,} miles")

        service = context.get("service_request", {})
        if service.get("type"):
            parts.append(f"✅ Service: {service['type']}")

        customer = context.get("customer_service_info", {})
        if customer.get("postcode"):
            parts.append(f"✅ Postcode: {customer['postcode']}")
        if customer.get("name"):
            parts.append(f"✅ Customer: {customer['name']}")
        if customer.get("phone"):
            parts.append(f"✅ Phone: {customer['phone']}")
        if customer.get("email"):
            parts.append(f"✅ Email: {customer['email']}")

        if context.get("selected_provider"):
            provider = context["selected_provider"]
            parts.append(f"✅ Provider: {provider['name']}")

        if context.get("appointment_date"):
            apt_date = context["appointment_date"]
            parts.append(f"✅ Date: {apt_date.get('display', '')}")

        if context.get("appointment_created"):
            parts.append(f"✅ APPOINTMENT BOOKED - Session cleared after booking")

        return "\n".join(parts)

    def _create_service_appointment(self, context: Dict) -> Dict[str, Any]:
        """Create appointment in database"""
        try:
            from service_appointment_manager import service_appointment_manager

            vehicle = context.get("vehicle_info", {})
            service_req = context.get("service_request", {})
            provider = context.get("selected_provider", {})
            date_info = context.get("appointment_date", {})
            customer = context.get("customer_service_info", {})

            print(f"\n🔥 CREATING APPOINTMENT:")
            print(f"   Vehicle: {vehicle.get('make')} {vehicle.get('model')}")
            print(f"   Customer: {customer.get('name')} - {customer.get('email')}")
            print(f"   Date: {date_info.get('date')} at {date_info.get('time')}")
            print(f"   Provider: {provider.get('name')}")

            customer["session_id"] = context.get("session_id", "")

            result = service_appointment_manager.create_appointment(
                vehicle=vehicle,
                service_type=service_req.get("type"),
                service_description=service_req.get("description"),
                urgency=service_req.get("urgency", "routine"),
                provider=provider,
                appointment_date=date_info.get("date"),
                appointment_time=date_info.get("time", "09:00"),
                customer=customer,
                recommendations=context.get("service_recommendations", {}),
            )

            return result

        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"Error: {str(e)}"}

    def _validate_appointment_data(self, context: Dict) -> Dict[str, Any]:
        """Validate all required appointment data before saving"""
        errors = []

        vehicle = context.get("vehicle_info", {})
        if not vehicle.get("make"):
            errors.append("Vehicle make not specified")
        if not vehicle.get("model"):
            errors.append("Vehicle model not specified")

        service = context.get("service_request", {})
        if not service.get("type"):
            errors.append("Service type not specified")

        provider = context.get("selected_provider", {})
        if not provider.get("name"):
            errors.append("Service provider not selected")

        date_info = context.get("appointment_date", {})
        if not date_info.get("date"):
            errors.append("Appointment date not selected")
        if not date_info.get("time"):
            errors.append("Appointment time not selected")

        customer = context.get("customer_service_info", {})
        if not customer.get("name"):
            errors.append("Customer name not provided")
        if not customer.get("email"):
            errors.append("Customer email not provided")
        if not customer.get("phone"):
            errors.append("Customer phone not provided")

        return {"valid": len(errors) == 0, "errors": errors}

    def _clear_session_context(
        self, context: Dict, appointment_id: str
    ) -> Dict[str, Any]:
        """Clear all service context to start fresh conversation"""
        cleared_context = {
            "session_id": context.get("session_id"),
            "routed": False,
            "active_agent": None,
            "appointment_created": False,
            "service_stage": "vehicle_identification",
            "vehicle_info": {},
            "service_request": {},
            "selected_provider": None,
            "appointment_date": {},
            "customer_service_info": {},
            "available_providers": None,
            "available_slots": None,
            "service_recommendations": {},
            "last_completed_appointment_id": appointment_id,
        }

        return cleared_context

    def _extract_appointment_from_history(
        self, messages: List[Any], context: Dict
    ) -> None:
        """Extract appointment details from conversation history (AI responses)"""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                text = msg.content

                vehicle_match = re.search(
                    r"Vehicle:\s*([A-Za-z\s]+?)\s*$$(\d{4})$$", text
                )
                if vehicle_match and not context["vehicle_info"].get("make"):
                    parts = vehicle_match.group(1).strip().split()
                    if parts:
                        context["vehicle_info"]["make"] = parts[0]
                        if len(parts) > 1:
                            context["vehicle_info"]["model"] = " ".join(parts[1:])
                        context["vehicle_info"]["year"] = int(vehicle_match.group(2))
                        print(
                            f"✅ Extracted vehicle: {context['vehicle_info']['make']} {context['vehicle_info']['model']} ({context['vehicle_info']['year']})"
                        )

                mileage_match = re.search(r"Mileage:\s*(\d+(?:,\d+)*)\s*miles", text)
                if mileage_match and not context["vehicle_info"].get("mileage"):
                    context["vehicle_info"]["mileage"] = int(
                        mileage_match.group(1).replace(",", "")
                    )
                    print(
                        f"✅ Extracted mileage: {context['vehicle_info']['mileage']} miles"
                    )

                service_match = re.search(r"Service:\s*([^\n-]+)", text)
                if service_match and not context["service_request"].get("type"):
                    service_raw = service_match.group(1).strip()
                    context["service_request"]["type"] = service_raw
                    context["service_request"]["description"] = service_raw
                    print(f"✅ Extracted service: {service_raw}")

                provider_match = re.search(
                    r"Provider:\s*([^\n-]+?)(?:\s*—|\s*\(|$)", text
                )
                if provider_match and not context.get("selected_provider"):
                    provider_name = provider_match.group(1).strip()
                    context["selected_provider"] = {
                        "name": provider_name,
                        "location": "Selected",
                        "tier": 2,
                    }
                    print(f"✅ Extracted provider: {provider_name}")

                date_patterns = [
                    r"Date:\s*([A-Za-z]+\s+[A-Za-z]+\s+\d+,?\s+\d{4})\s*—\s*(\d{1,2}:\d{2})",  # Wed Jan 21, 2026 — 10:30
                    r"Date:\s*([A-Za-z]+\s+[A-Za-z]+\s+\d+,?\s+\d{4})\s*$$[^)]*$$",  # Wed Jan 21, 2026 (London time)
                ]
                for pattern in date_patterns:
                    date_match = re.search(pattern, text)
                    if date_match and not context.get("appointment_date"):
                        date_str = date_match.group(1).strip()
                        # Extract time if available
                        time_match = re.search(
                            r"(\d{1,2}):(\d{2})",
                            text[date_match.start() : date_match.end() + 20],
                        )
                        time_str = (
                            time_match.group(0).strip() if time_match else "09:00"
                        )

                        # Convert date to YYYY-MM-DD format
                        try:
                            from datetime import datetime

                            dt = datetime.strptime(
                                date_str.replace(",", ""), "%a %b %d %Y"
                            )
                            formatted_date = dt.strftime("%Y-%m-%d")
                        except:
                            formatted_date = date_str

                        context["appointment_date"] = {
                            "date": formatted_date,
                            "time": time_str,
                            "display": f"{date_str} at {time_str}",
                        }
                        print(f"✅ Extracted date: {formatted_date} at {time_str}")
                        break

                postcode_match = re.search(
                    r"Postcode:\s*([A-Z0-9\s]+?)(?:\n|-|$)", text
                )
                if postcode_match and not context["customer_service_info"].get(
                    "postcode"
                ):
                    context["customer_service_info"]["postcode"] = postcode_match.group(
                        1
                    ).strip()
                    print(
                        f"✅ Extracted postcode: {context['customer_service_info']['postcode']}"
                    )

                customer_match = re.search(
                    r"Customer:\s*([A-Za-z\s]+?)(?:\s*-|\n|$)", text
                )
                if customer_match and not context["customer_service_info"].get("name"):
                    context["customer_service_info"]["name"] = customer_match.group(
                        1
                    ).strip()
                    print(
                        f"✅ Extracted customer: {context['customer_service_info']['name']}"
                    )

                phone_match = re.search(r"Phone:\s*(\+?\d[\d\s\-()]+?)(?:\n|-|$)", text)
                if phone_match and not context["customer_service_info"].get("phone"):
                    context["customer_service_info"]["phone"] = phone_match.group(
                        1
                    ).strip()
                    print(
                        f"✅ Extracted phone: {context['customer_service_info']['phone']}"
                    )

                email_match = re.search(
                    r"Email:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})", text
                )
                if email_match and not context["customer_service_info"].get("email"):
                    context["customer_service_info"]["email"] = email_match.group(
                        1
                    ).strip()
                    print(
                        f"✅ Extracted email: {context['customer_service_info']['email']}"
                    )


# Singleton
phase2_service_manager = Phase2ServiceManager()
