"""
Raava AI Service Manager - Phase 2 ENHANCED
Complete CONFIRM → Validate → Save → Email → Clear Session flow with logging
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


class Phase2ServiceManagerEnhanced:
    """Raava AI Service Manager with enhanced confirmation flow"""

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
        """Process service request with complete confirmation flow"""
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
        print(self._is_user_confirming(last_user_message, session_context))
        if self._is_user_confirming(last_user_message, session_context):
            print("\n" + "=" * 70)
            print("✅ USER CONFIRMED - STARTING CONFIRMATION FLOW")
            print("=" * 70)

            # Step 1: Validate all data
            validation_result = self._validate_all_data(session_context)
            if not validation_result["valid"]:
                print(f"❌ Validation failed: {validation_result['errors']}")
                return {
                    "messages": [
                        AIMessage(
                            content=f"Please provide: {', '.join(validation_result['errors'])}"
                        )
                    ],
                    "context": session_context,
                }

            print("✅ Step 1 COMPLETE: All data validated")

            # Step 2: Create and save appointment to database
            save_result = await self._save_appointment_to_db(session_context)
            if not save_result["success"]:
                print(f"❌ Database save failed: {save_result['message']}")
                return {
                    "messages": [
                        AIMessage(
                            content=f"Error saving appointment: {save_result['message']}"
                        )
                    ],
                    "context": session_context,
                }

            appointment_id = save_result["appointment_id"]
            print(f"✅ Step 2 COMPLETE: Appointment saved - {appointment_id}")

            # Step 3: Send confirmation email
            email_result = await self._send_confirmation_email(
                session_context, save_result["appointment"]
            )
            if email_result["sent"]:
                print(f"✅ Step 3 COMPLETE: Confirmation email sent")
            else:
                print(f"⚠️ Step 3 WARNING: Email not sent - {email_result['reason']}")

            # Step 4: Clear session for fresh conversation
            clear_result = self._clear_session_for_new_conversation(session_context)
            print(f"✅ Step 4 COMPLETE: Session cleared for fresh conversation")

            print("=" * 70)
            print("✅ CONFIRMATION FLOW COMPLETED SUCCESSFULLY")
            print("=" * 70 + "\n")

            # Return success message with appointment details
            response_message = save_result.get(
                "confirmation_message", "APPOINTMENT BOOKED"
            )

            return {
                "messages": [AIMessage(content=response_message)],
                "context": session_context,
                "appointment_created": True,
                "appointment_id": appointment_id,
            }

    def _validate_all_data(self, context: Dict) -> Dict[str, Any]:
        """Validate all required appointment data"""
        print("\n📋 VALIDATING ALL DATA:")
        errors = []

        vehicle = context.get("vehicle_info", {})
        service = context.get("service_request", {})
        provider = context.get("selected_provider")
        date_info = context.get("appointment_date")
        customer = context.get("customer_service_info", {})

        # Validate vehicle
        if not vehicle.get("make"):
            errors.append("Vehicle make")
            print("  ❌ Missing: Vehicle make")
        else:
            print(
                f"  ✅ Vehicle: {vehicle['make']} {vehicle.get('model', '')} ({vehicle.get('year', '')})"
            )

        if not vehicle.get("mileage"):
            errors.append("Vehicle mileage")
            print("  ❌ Missing: Vehicle mileage")
        else:
            print(f"  ✅ Mileage: {vehicle['mileage']:,} miles")

        # Validate service
        if not service.get("type"):
            errors.append("Service type")
            print("  ❌ Missing: Service type")
        else:
            print(f"  ✅ Service: {service['type']}")

        # Validate provider
        if not provider:
            errors.append("Service provider")
            print("  ❌ Missing: Service provider")
        else:
            print(f"  ✅ Provider: {provider.get('name', 'Unknown')}")

        # Validate date
        if not date_info:
            errors.append("Appointment date")
            print("  ❌ Missing: Appointment date")
        else:
            print(f"  ✅ Date: {date_info.get('display', date_info.get('date'))}")

        # Validate customer
        if not customer.get("name"):
            errors.append("Customer name")
            print("  ❌ Missing: Customer name")
        else:
            print(f"  ✅ Name: {customer['name']}")

        if not customer.get("email"):
            errors.append("Customer email")
            print("  ❌ Missing: Customer email")
        else:
            print(f"  ✅ Email: {customer['email']}")

        if not customer.get("phone"):
            errors.append("Customer phone")
            print("  ❌ Missing: Customer phone")
        else:
            print(f"  ✅ Phone: {customer['phone']}")

        if not customer.get("postcode"):
            errors.append("Customer postcode")
            print("  ❌ Missing: Customer postcode")
        else:
            print(f"  ✅ Postcode: {customer['postcode']}")

        valid = len(errors) == 0
        print(
            f"\n{'✅ ALL DATA VALID' if valid else f'❌ {len(errors)} ERRORS FOUND'}\n"
        )

        return {"valid": valid, "errors": errors}

    async def _save_appointment_to_db(self, context: Dict) -> Dict[str, Any]:
        """Save appointment to database with logging"""
        print("\n💾 SAVING APPOINTMENT TO DATABASE:")
        try:
            from service_booking_manager import service_appointment_manager

            vehicle = context.get("vehicle_info", {})
            service_req = context.get("service_request", {})
            provider = context.get("selected_provider", {})
            date_info = context.get("appointment_date", {})
            customer = context.get("customer_service_info", {})

            print(f"  📝 Vehicle: {vehicle.get('make')} {vehicle.get('model')}")
            print(f"  👤 Customer: {customer.get('name')} ({customer.get('email')})")
            print(f"  🏢 Provider: {provider.get('name')}")
            print(f"  📅 Date: {date_info.get('date')} at {date_info.get('time')}")

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

            if result.get("success"):
                print(f"  ✅ Successfully saved: {result.get('appointment_id')}")
                return {
                    "success": True,
                    "appointment_id": result.get("appointment_id"),
                    "appointment": result.get("appointment"),
                    "confirmation_message": result.get("message"),
                }
            else:
                print(f"  ❌ Database error: {result.get('message')}")
                return {
                    "success": False,
                    "message": result.get("message", "Unknown error"),
                }

        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"Error: {str(e)}"}

    async def _send_confirmation_email(
        self, context: Dict, appointment: Dict
    ) -> Dict[str, Any]:
        """Send confirmation email with logging"""
        print("\n📧 SENDING CONFIRMATION EMAIL:")
        try:
            from enhanced_email_service import enhanced_email_service

            customer_email = context.get("customer_service_info", {}).get("email")
            print(f"  📬 Recipient: {customer_email}")

            result = enhanced_email_service.send_appointment_confirmation(appointment)

            if result:
                print(f"  ✅ Email sent successfully")
                return {"sent": True, "reason": "Email sent"}
            else:
                print(f"  ⚠️ Email service returned False - check SMTP configuration")
                return {
                    "sent": False,
                    "reason": "Email service returned False - check SMTP configuration",
                }

        except Exception as e:
            print(f"  ❌ EMAIL EXCEPTION: {e}")
            import traceback

            traceback.print_exc()
            return {"sent": False, "reason": f"Exception: {str(e)}"}

    def _clear_session_for_new_conversation(self, context: Dict) -> Dict[str, Any]:
        """Clear session data for fresh conversation"""
        print("\n🧹 CLEARING SESSION FOR FRESH CONVERSATION:")

        # Reset all service-related context
        context["service_stage"] = "vehicle_identification"
        context["vehicle_info"] = {}
        context["service_request"] = {}
        context["customer_service_info"] = {}
        context["selected_provider"] = None
        context["appointment_date"] = None
        context["available_providers"] = []
        context["available_slots"] = []
        context["service_recommendations"] = {}

        # Keep session tracking data
        context["appointment_completed"] = True
        context["last_appointment_created"] = datetime.utcnow().isoformat()

        print(f"  ✅ Service context cleared")
        print(f"  ✅ Session ready for new conversation")

        return {"success": True, "cleared": True}

    def _is_user_confirming(self, text: str, context: Dict) -> bool:
        """Check if user is confirming the appointment"""
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


# Singleton
phase2_service_manager_enhanced = Phase2ServiceManagerEnhanced()
