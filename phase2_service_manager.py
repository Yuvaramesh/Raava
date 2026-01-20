"""
Raava AI Service Manager - Natural Conversational Style
Human-like service booking experience with immediate appointment creation
"""

import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import OPENAI_API_KEY, LLM_MODEL_NAME, LLM_TEMPERATURE
from datetime import datetime, timedelta
import re


class phase2_service_manager:
    """Raava AI Service Manager - Natural conversation flow"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=0.7,  # Higher for more natural responses
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are a warm, friendly service advisor at Raava - like talking to a helpful friend who really knows cars.

🎯 CONVERSATION STYLE:
- Sound human, natural, and conversational
- Use casual, friendly language
- Show genuine interest in their vehicle
- Be enthusiastic about helping them
- Never sound robotic or scripted
- Ask questions naturally, not like a form

💬 CONVERSATION FLOW (ask ONE question at a time):

**Vehicle Information (casual & interested):**
1. Make → "Nice! What make is your car?" or "What kind of car do you have?"
2. Model → "Sweet! Which model?" or "Ah, what model is it?"
3. Year → "And what year?" or "Which year?"
4. Mileage → "How many miles has it done?" or "What's the current mileage?"
5. Service Type → "What kind of service does it need?" or "What brings it in today?"

**Customer Details (friendly & personal):**
6. Name → "Perfect! And what's your name?" or "Great! Who am I speaking with?"
7. Email → "What's the best email to send the confirmation to?"
8. Phone → "And a contact number?"
9. Postcode → "What's your postcode? I'll find the best service centers near you."

**Provider Selection:**
10. Show providers naturally with personality
11. Ask: "Which one works best for you?"

**Scheduling:**
12. Date/Time → "When would you like to bring it in?"

**After date/time is provided - IMMEDIATELY CREATE APPOINTMENT**
- Don't ask for confirmation
- Don't repeat any information
- Just create the appointment, send email, and confirm it's done

**TONE EXAMPLES:**

❌ BAD (Robotic):
"What make is your vehicle? (e.g., Toyota, Ford, Honda)"
"Current mileage?"
"Your postcode?"

✅ GOOD (Natural):
"Nice! What kind of car are we looking after?"
"How many miles has she done?"
"What's your postcode so I can find you the best places nearby?"

**After collecting postcode, present providers like this:**

"Alright, I've found some great options near you in [area]:

1. **Autoshield** - Cuffley (16 miles away)
   • Lamborghini specialists with ex-factory techs
   • 4.9⭐ rating • Around £325

2. **Performance Marques** - Surrey (20 miles)
   • Italian supercar experts
   • 4.8⭐ • About £340

3. **Elite Motors** - Manchester (longer drive, but excellent)
   • Supercar service center
   • 4.7⭐ • £375

Which one catches your eye?"

**CRITICAL RULES:**
- NEVER repeat questions already answered
- Progress forward systematically
- Be conversational and warm
- React naturally to their answers
- Show enthusiasm about their car
- Make recommendations when showing providers
- IMMEDIATELY create appointment after date/time without asking for confirmation

[Replied by: Raava Service Advisor]
"""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process with natural conversation flow"""
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
            session_context["service_stage"] = "vehicle_make"
            session_context["vehicle_info"] = {}
            session_context["service_request"] = {}
            session_context["customer_service_info"] = {}
            session_context["available_providers"] = []
            session_context["selected_provider"] = None
            session_context["appointment_date"] = None
            session_context["appointment_created"] = False

        stage = session_context.get("service_stage")
        print(f"\n🔧 STAGE: {stage}")
        print(f"📝 USER: {last_user_message}")

        # Check if already completed
        if session_context.get("appointment_created"):
            return {
                "messages": [
                    AIMessage(
                        content="Your appointment is all set! Is there anything else I can help you with? 😊"
                    )
                ],
                "context": session_context,
            }

        enhanced_context = ""

        # STAGE PROGRESSION - Natural conversation
        if stage == "vehicle_make":
            make = self._extract_make(last_user_message)
            if make:
                session_context["vehicle_info"]["make"] = make
                session_context["service_stage"] = "vehicle_model"
                enhanced_context = f"✅ Make: {make}\nNEXT: Ask naturally about the model. React positively to the make!"
            else:
                enhanced_context = (
                    "ASK: What kind of car do you have? Be friendly and interested!"
                )

        elif stage == "vehicle_model":
            model = last_user_message.strip()
            if len(model) > 1:
                session_context["vehicle_info"]["model"] = model
                session_context["service_stage"] = "vehicle_year"
                make = session_context["vehicle_info"].get("make", "")
                enhanced_context = f"✅ Model: {model}\nNEXT: Ask about year. Show enthusiasm about the {make} {model}!"

        elif stage == "vehicle_year":
            year = self._extract_year(last_user_message)
            if year:
                session_context["vehicle_info"]["year"] = year
                session_context["service_stage"] = "vehicle_mileage"
                enhanced_context = f"✅ Year: {year}\nNEXT: Ask about mileage naturally"

        elif stage == "vehicle_mileage":
            mileage = self._extract_mileage(last_user_message)
            if mileage is not None:
                session_context["vehicle_info"]["mileage"] = mileage
                session_context["service_stage"] = "service_type"
                enhanced_context = f"✅ Mileage: {mileage:,} miles\nNEXT: Ask what service they need, be conversational"

        elif stage == "service_type":
            session_context["service_request"] = {
                "type": "scheduled_service",
                "description": last_user_message.strip(),
                "urgency": "routine",
            }
            session_context["service_stage"] = "customer_name"
            enhanced_context = (
                "✅ Service noted\nNEXT: Ask for their name naturally and warmly"
            )

        elif stage == "customer_name":
            name = self._extract_name(last_user_message)
            if name:
                session_context["customer_service_info"]["name"] = name
                session_context["service_stage"] = "customer_email"
                enhanced_context = (
                    f"✅ Name: {name}\nNEXT: Ask for email address conversationally"
                )

        elif stage == "customer_email":
            email = self._extract_email(last_user_message)
            if email:
                session_context["customer_service_info"]["email"] = email
                session_context["service_stage"] = "customer_phone"
                enhanced_context = (
                    f"✅ Email: {email}\nNEXT: Ask for phone number naturally"
                )

        elif stage == "customer_phone":
            phone = self._extract_phone(last_user_message)
            if phone:
                session_context["customer_service_info"]["phone"] = phone
                session_context["service_stage"] = "customer_postcode"
                enhanced_context = f"✅ Phone: {phone}\nNEXT: Ask for postcode to find nearby providers"

        elif stage == "customer_postcode":
            postcode = self._extract_postcode(last_user_message)
            if postcode:
                session_context["customer_service_info"]["postcode"] = postcode

                # Load providers
                providers = self._search_service_providers(session_context)
                session_context["available_providers"] = providers
                session_context["service_stage"] = "provider_selection"

                vehicle = session_context["vehicle_info"]
                area = self._get_area_name(postcode)

                enhanced_context = f"✅ Postcode: {postcode}\n\n"
                enhanced_context += f"SHOW PROVIDERS CONVERSATIONALLY for {vehicle['make']} near {area}:\n\n"

                for i, p in enumerate(providers, 1):
                    enhanced_context += f"{i}. **{p['name']}** - {p['location']} ({p['distance_miles']} miles away)\n"
                    enhanced_context += (
                        f"   • {', '.join(p.get('specialties', ['Full service']))}\n"
                    )
                    enhanced_context += f"   • {p['rating']}⭐ rating • Around £{p['estimated_cost']}\n\n"

                enhanced_context += "\nPresent these naturally with personality! Make a recommendation based on the vehicle make."

        elif stage == "provider_selection":
            match = re.search(r"([1-3])", last_user_message)
            if match:
                idx = int(match.group(1)) - 1
                providers = session_context.get("available_providers", [])
                if 0 <= idx < len(providers):
                    session_context["selected_provider"] = providers[idx]
                    session_context["service_stage"] = "appointment_date"
                    provider_name = providers[idx]["name"]
                    enhanced_context = f"✅ Provider: {provider_name}\nNEXT: Ask when they'd like to bring it in. Be casual and helpful!"

        elif stage == "appointment_date":
            date_info = self._parse_appointment_date(last_user_message)
            if date_info:
                session_context["appointment_date"] = date_info

                # IMMEDIATELY CREATE APPOINTMENT - NO CONFIRMATION NEEDED
                print("\n🚀 AUTO-CREATING APPOINTMENT NOW...")

                result = self._create_appointment_now(session_context)

                if result.get("success"):
                    session_context["appointment_created"] = True
                    session_context["appointment_id"] = result.get("appointment_id")

                    # Generate natural confirmation message
                    vehicle = session_context["vehicle_info"]
                    provider = session_context["selected_provider"]
                    apt_date = session_context["appointment_date"]
                    customer = session_context["customer_service_info"]
                    apt_id = result["appointment_id"]

                    confirmation_msg = f"""Perfect! You're all booked! 🎉

**Appointment ID:** {apt_id}

Your {vehicle['year']} {vehicle['make']} {vehicle['model']} is scheduled with **{provider['name']}** on **{apt_date['formatted']}**.

I've just sent a confirmation email to **{customer['email']}** with all the details, including:
• Service location and directions
• What to bring (service book, ID, etc.)
• Provider contact: {provider['phone']}

They'll give you a call the day before to confirm. The {customer.get('service_request', {}).get('description', 'service')} usually takes 2-4 hours.

**Quick tip:** Try to arrive about 10 minutes early, and they'll take great care of your {vehicle['make']}!

Need anything else? 😊"""

                    return {
                        "messages": [AIMessage(content=confirmation_msg)],
                        "context": session_context,
                    }
                else:
                    # Error creating appointment
                    error_msg = f"Oops! Something went wrong creating your appointment. Could you try again or call {session_context['selected_provider']['phone']} directly? Sorry about that!"
                    return {
                        "messages": [AIMessage(content=error_msg)],
                        "context": session_context,
                    }

        # Build LLM conversation
        conversation_messages = [
            SystemMessage(content=self.system_prompt + "\n\n" + enhanced_context)
        ]

        for msg in messages[-6:]:  # More context for natural conversation
            conversation_messages.append(msg)

        # Get response
        response = await self.llm.ainvoke(conversation_messages)
        response_text = response.content

        return {
            "messages": [AIMessage(content=response_text)],
            "context": session_context,
        }

    def _extract_make(self, text: str) -> Optional[str]:
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
            "Bentley",
        ]
        text_lower = text.lower()
        for make in makes:
            if make.lower() in text_lower:
                return make
        return None

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year"""
        match = re.search(r"(20\d{2})", text)
        if match:
            year = int(match.group(1))
            if 2000 <= year <= datetime.now().year + 1:
                return year
        return None

    def _extract_mileage(self, text: str) -> Optional[int]:
        """Extract mileage"""
        match = re.search(r"(\d+)\s*(?:k|miles)?", text.lower())
        if match:
            value = int(match.group(1))
            if "k" in text.lower():
                value *= 1000
            return value
        return None

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name"""
        words = text.split()
        name_words = [
            w
            for w in words
            if w.lower() not in ["my", "name", "is", "i'm", "hi", "hello"]
            and len(w) > 1
        ]
        if name_words:
            return " ".join(name_words[:2]).title()
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email"""
        match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone"""
        match = re.search(r"(\+?\d{10,15})", text)
        return match.group(0) if match else None

    def _extract_postcode(self, text: str) -> Optional[str]:
        """Extract UK postcode"""
        match = re.search(
            r"\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b", text, re.IGNORECASE
        )
        return match.group(0).upper() if match else None

    def _get_area_name(self, postcode: str) -> str:
        """Get area name from postcode"""
        area_map = {
            "SW": "Southwest London",
            "W1": "West London",
            "EC": "Central London",
            "NW": "Northwest London",
        }
        area_code = "".join([c for c in postcode if c.isalpha()])[:2].upper()
        return area_map.get(area_code, "your area")

    def _search_service_providers(self, context: Dict) -> List[Dict]:
        """Get service providers with specialties"""
        make = context["vehicle_info"].get("make", "")

        # Real providers from service_providers.py data
        if make == "Lamborghini":
            return [
                {
                    "name": "Autoshield",
                    "location": "Cuffley, Hertfordshire",
                    "distance_miles": 15.6,
                    "rating": 4.9,
                    "phone": "01707 888890",
                    "estimated_cost": 325,
                    "specialties": [
                        "Lamborghini specialist",
                        "Ex-factory technicians",
                        "Performance service",
                    ],
                },
                {
                    "name": "Performance Marques",
                    "location": "Surrey",
                    "distance_miles": 20.2,
                    "rating": 4.8,
                    "phone": "01483 234567",
                    "estimated_cost": 340,
                    "specialties": [
                        "Italian supercar specialist",
                        "Service & MOT",
                        "Upgrades",
                    ],
                },
                {
                    "name": "Elite Motors",
                    "location": "Manchester",
                    "distance_miles": 180.5,
                    "rating": 4.7,
                    "phone": "0161 123 4567",
                    "estimated_cost": 375,
                    "specialties": [
                        "Supercar service center",
                        "Track preparation",
                    ],
                },
            ]
        else:
            # Default providers
            return [
                {
                    "name": "Premium Auto Care",
                    "location": "Central London",
                    "distance_miles": 5.2,
                    "rating": 4.8,
                    "phone": "020 1234 5678",
                    "estimated_cost": 450,
                    "specialties": ["Luxury vehicle specialist", "Full service"],
                },
                {
                    "name": "Elite Motors",
                    "location": "West London",
                    "distance_miles": 8.5,
                    "rating": 4.7,
                    "phone": "020 8765 4321",
                    "estimated_cost": 375,
                    "specialties": ["Performance cars", "Track prep"],
                },
                {
                    "name": "City Car Service",
                    "location": "Southeast London",
                    "distance_miles": 12.0,
                    "rating": 4.6,
                    "phone": "020 5555 1234",
                    "estimated_cost": 325,
                    "specialties": ["General service", "MOT testing"],
                },
            ]

    def _parse_appointment_date(self, text: str) -> Optional[Dict]:
        """Parse date and time"""
        text_lower = text.lower()
        now = datetime.now()

        # Default time
        hour, minute = 10, 0

        # Extract date
        date = None

        # Format 1: "22 jan 2026" or "22 january 2026"
        date_match = re.search(
            r"(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:uary|ruary|ch|il|e|y)?(?:\s+(\d{4}))?",
            text_lower,
        )
        if date_match:
            day = int(date_match.group(1))
            month_map = {
                "jan": 1,
                "feb": 2,
                "mar": 3,
                "apr": 4,
                "may": 5,
                "jun": 6,
                "jul": 7,
                "aug": 8,
                "sep": 9,
                "oct": 10,
                "nov": 11,
                "dec": 12,
            }
            month_str = date_match.group(2)[:3]  # Get first 3 letters
            month = month_map.get(month_str)
            year = int(date_match.group(3)) if date_match.group(3) else now.year
            if month:
                date = datetime(year, month, day)

        # Format 2: Relative dates
        elif "tomorrow" in text_lower:
            date = now + timedelta(days=1)
        elif "next week" in text_lower:
            date = now + timedelta(days=7)

        if not date:
            date = now + timedelta(days=1)  # Default to tomorrow

        # Extract time: "11:30", "11.30", "11:30AM", "2pm"
        time_match = re.search(r"(\d{1,2})[.:](\d{2})", text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            if "pm" in text_lower and hour < 12:
                hour += 12
            elif "am" in text_lower and hour == 12:
                hour = 0
        elif re.search(r"(\d{1,2})\s*(am|pm)", text_lower):
            match = re.search(r"(\d{1,2})\s*(am|pm)", text_lower)
            hour = int(match.group(1))
            if match.group(2) == "pm" and hour < 12:
                hour += 12
            elif match.group(2) == "am" and hour == 12:
                hour = 0

        date = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return {
            "datetime": date,
            "formatted": date.strftime("%A, %d %B %Y at %I:%M %p"),
        }

    def _create_appointment_now(self, context: Dict) -> Dict[str, Any]:
        """Create appointment in Services collection and send email"""
        try:
            from service_booking_manager import service_booking_manager

            vehicle = context.get("vehicle_info", {})
            service = context.get("service_request", {})
            customer = context.get("customer_service_info", {})
            provider = context.get("selected_provider", {})
            date = context.get("appointment_date", {})

            print(f"\n🔥 CREATING APPOINTMENT:")
            print(
                f"   Vehicle: {vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('year')})"
            )
            print(f"   Customer: {customer.get('name')} - {customer.get('email')}")
            print(f"   Provider: {provider.get('name')}")
            print(f"   Date: {date.get('formatted')}")

            result = service_booking_manager.create_service_appointment(
                vehicle_info=vehicle,
                service_request=service,
                customer_info=customer,
                provider_info=provider,
                appointment_datetime=date.get("datetime"),
            )

            if result.get("success"):
                print(f"✅ APPOINTMENT CREATED: {result.get('appointment_id')}")
                print(f"✅ EMAIL SENT TO: {customer.get('email')}")

            return result

        except Exception as e:
            print(f"❌ ERROR CREATING APPOINTMENT: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"Error: {str(e)}"}


# Singleton
phase2_service_manager = phase2_service_manager()
