"""
Service Appointment Manager - FIXED
Saves appointments to Services collection and sends confirmation emails
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid


class ServiceAppointmentManager:
    """Manages service appointments in Services collection"""

    def __init__(self):
        self._collection = None

    def _get_collection(self):
        """Lazy load Services collection"""
        if self._collection is None:
            try:
                from database import db

                if db is not None:
                    self._collection = db["Services"]  # ✅ Correct collection name
                    # Create indexes
                    try:
                        self._collection.create_index(
                            [("appointment_id", 1)], unique=True
                        )
                        self._collection.create_index([("customer.email", 1)])
                        self._collection.create_index([("created_at", -1)])
                        self._collection.create_index([("status", 1)])
                        print("✅ Services collection indexes created")
                    except Exception as e:
                        print(f"ℹ️ Indexes may already exist: {e}")
            except Exception as e:
                print(f"⚠️ Could not load Services collection: {e}")
        return self._collection

    def create_appointment(
        self,
        vehicle: Dict[str, Any],
        service_type: str,
        service_description: str,
        urgency: str,
        provider: Dict[str, Any],
        appointment_date: str,
        appointment_time: str,
        customer: Dict[str, Any],
        recommendations: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create service appointment and save to Services collection
        """
        try:
            print("\n🔧 CREATING SERVICE APPOINTMENT")
            print("=" * 70)

            # Generate appointment ID
            appointment_id = self._generate_appointment_id()
            print(f"📋 Appointment ID: {appointment_id}")

            # Parse date
            try:
                apt_datetime = datetime.strptime(
                    f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M"
                )
            except:
                apt_datetime = datetime.now() + timedelta(days=1)

            # Build appointment document
            appointment = {
                "appointment_id": appointment_id,
                "status": "pending",
                # Vehicle information
                "vehicle": {
                    "make": vehicle.get("make", ""),
                    "model": vehicle.get("model", ""),
                    "year": vehicle.get("year", ""),
                    "mileage": vehicle.get("mileage", 0),
                    "registration": vehicle.get("registration", ""),
                },
                # Service details
                "service": {
                    "type": service_type,
                    "description": service_description,
                    "urgency": urgency,
                    "estimated_duration_hours": self._estimate_duration(service_type),
                    "estimated_cost_min": (
                        recommendations.get("total_cost_estimate", {}).get("min", 0)
                        if recommendations
                        else 0
                    ),
                    "estimated_cost_max": (
                        recommendations.get("total_cost_estimate", {}).get("max", 0)
                        if recommendations
                        else provider.get("estimated_cost", 500)
                    ),
                },
                # Provider information
                "provider": {
                    "name": provider.get("name", ""),
                    "location": provider.get("location", ""),
                    "tier": provider.get("tier", 2),
                    "phone": provider.get("phone", ""),
                    "rating": provider.get("rating", 0),
                    "distance_miles": provider.get("distance_miles", 0),
                },
                # Appointment timing
                "appointment": {
                    "date": appointment_date,
                    "time": appointment_time,
                    "datetime": apt_datetime,
                    "duration_estimate": f"{self._estimate_duration(service_type)} hours",
                },
                # Customer information
                "customer": {
                    "name": customer.get("name", ""),
                    "email": customer.get("email", ""),
                    "phone": customer.get("phone", ""),
                    "postcode": customer.get("postcode", ""),
                },
                # Service recommendations
                "recommendations": recommendations or {},
                # Metadata
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "session_id": customer.get("session_id", ""),
                "notes": [],
                "reminders_sent": [],
                "email_sent": False,
                "email_sent_at": None,
            }

            print(
                f"🚗 Vehicle: {appointment['vehicle']['make']} {appointment['vehicle']['model']}"
            )
            print(
                f"👤 Customer: {appointment['customer']['name']} ({appointment['customer']['email']})"
            )
            print(f"🔧 Service: {appointment['service']['type']}")
            print(
                f"📅 Date: {appointment['appointment']['date']} at {appointment['appointment']['time']}"
            )

            # 🔥 SAVE TO DATABASE (Services collection)
            col = self._get_collection()
            if col is not None:
                result = col.insert_one(appointment)
                appointment["_id"] = str(result.inserted_id)
                print(f"\n✅ SAVED TO SERVICES COLLECTION")
                print(f"   Document ID: {result.inserted_id}")

                # 🔥 VERIFY IT WAS SAVED
                verify = col.find_one({"appointment_id": appointment_id})
                if verify:
                    print(f"✅ VERIFIED: Appointment exists in Services collection")
                    print(f"   Collection: {col.name}")
                    print(f"   Document count: {col.count_documents({})}")
                else:
                    print(f"❌ ERROR: Appointment not found after insertion!")
                    return {
                        "success": False,
                        "message": "Failed to verify appointment in database",
                    }
            else:
                print("⚠️ Running without database - appointment not persisted")
                return {"success": False, "message": "Database not available"}

            # 🔥 SEND EMAIL CONFIRMATION
            email_sent = self._send_appointment_email(appointment)

            if email_sent:
                # Update appointment with email status
                col.update_one(
                    {"appointment_id": appointment_id},
                    {"$set": {"email_sent": True, "email_sent_at": datetime.utcnow()}},
                )
                print(f"✅ EMAIL CONFIRMATION SENT")
            else:
                print(f"⚠️ Email not sent (check SMTP configuration)")

            # Generate confirmation message
            message = self._generate_confirmation_message(appointment)

            print("=" * 70)
            print("✅ APPOINTMENT CREATION COMPLETE\n")

            return {
                "success": True,
                "appointment_id": appointment_id,
                "appointment": appointment,
                "message": message,
                "email_sent": email_sent,
            }

        except Exception as e:
            print(f"❌ ERROR CREATING APPOINTMENT: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "message": f"Failed to create appointment: {str(e)}",
            }

    def _send_appointment_email(self, appointment: Dict[str, Any]) -> bool:
        """Send appointment confirmation email"""
        try:
            from enhanced_email_service import enhanced_email_service

            customer_email = appointment["customer"]["email"]
            if not customer_email:
                print("⚠️ No customer email provided")
                return False

            print(f"\n📧 SENDING EMAIL TO: {customer_email}")

            # Send email using the enhanced email service
            result = enhanced_email_service.send_service_appointment_confirmation(
                appointment
            )

            return result

        except Exception as e:
            print(f"❌ Email send error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def get_appointment(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve appointment by ID"""
        try:
            col = self._get_collection()
            if col is not None:
                appointment = col.find_one({"appointment_id": appointment_id})
                if appointment:
                    appointment["_id"] = str(appointment["_id"])
                return appointment
        except Exception as e:
            print(f"❌ Error retrieving appointment: {e}")
        return None

    def update_appointment_status(
        self, appointment_id: str, status: str, note: Optional[str] = None
    ) -> bool:
        """Update appointment status"""
        valid_statuses = [
            "pending",
            "confirmed",
            "in_progress",
            "completed",
            "cancelled",
        ]
        if status not in valid_statuses:
            return False

        try:
            col = self._get_collection()
            if col is not None:
                update_data = {"status": status, "updated_at": datetime.utcnow()}

                if note:
                    col.update_one(
                        {"appointment_id": appointment_id},
                        {
                            "$set": update_data,
                            "$push": {
                                "notes": {
                                    "timestamp": datetime.utcnow(),
                                    "note": note,
                                    "status": status,
                                }
                            },
                        },
                    )
                else:
                    col.update_one(
                        {"appointment_id": appointment_id}, {"$set": update_data}
                    )
                return True
        except Exception as e:
            print(f"❌ Error updating appointment: {e}")
        return False

    def get_customer_appointments(
        self, email: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get all appointments for a customer"""
        try:
            col = self._get_collection()
            if col is not None:
                appointments = (
                    col.find({"customer.email": email})
                    .sort("created_at", -1)
                    .limit(limit)
                )
                return [self._serialize_appointment(apt) for apt in appointments]
        except Exception as e:
            print(f"❌ Error retrieving appointments: {e}")
        return []

    def _generate_appointment_id(self) -> str:
        """Generate unique appointment ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique = str(uuid.uuid4())[:8].upper()
        return f"SRV-RA-{timestamp[:4]}-{unique[:5]}"

    def _estimate_duration(self, service_type: str) -> float:
        """Estimate service duration in hours"""
        durations = {
            "scheduled_service": 2.0,
            "minor_service": 1.5,
            "major_service": 3.0,
            "repair": 2.5,
            "upgrade": 4.0,
            "inspection": 1.0,
            "mot": 1.0,
            "brake_service": 2.0,
            "tire_service": 1.0,
        }
        return durations.get(service_type, 2.0)

    def _serialize_appointment(self, appointment: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        appointment["_id"] = str(appointment["_id"])

        # Convert datetime objects
        for field in ["created_at", "updated_at"]:
            if field in appointment and isinstance(appointment[field], datetime):
                appointment[field] = appointment[field].isoformat()

        if "appointment" in appointment and "datetime" in appointment["appointment"]:
            if isinstance(appointment["appointment"]["datetime"], datetime):
                appointment["appointment"]["datetime"] = appointment["appointment"][
                    "datetime"
                ].isoformat()

        return appointment

    def _generate_confirmation_message(self, appointment: Dict[str, Any]) -> str:
        """Generate appointment confirmation message"""
        apt_id = appointment["appointment_id"]
        vehicle = appointment["vehicle"]
        service = appointment["service"]
        provider = appointment["provider"]
        apt_info = appointment["appointment"]
        customer = appointment["customer"]

        # Format datetime
        try:
            apt_dt = datetime.strptime(
                f"{apt_info['date']} {apt_info['time']}", "%Y-%m-%d %H:%M"
            )
            formatted_date = apt_dt.strftime("%A, %d %B %Y")
            formatted_time = apt_dt.strftime("%I:%M %p")
        except:
            formatted_date = apt_info["date"]
            formatted_time = apt_info["time"]

        # Urgency emoji
        urgency_emoji = {
            "urgent": "🚨",
            "soon": "⚠️",
            "routine": "📅",
        }
        urgency_symbol = urgency_emoji.get(service["urgency"], "📅")

        # Cost range
        cost_min = service.get("estimated_cost_min", 0)
        cost_max = service.get("estimated_cost_max", 0)
        if cost_max > 0:
            cost_display = f"£{cost_min:,.0f} - £{cost_max:,.0f}"
        else:
            cost_display = "TBC"

        message = f"""✅ **SERVICE APPOINTMENT CONFIRMED**

**Appointment ID:** {apt_id}

🚗 **VEHICLE:**
{vehicle['make']} {vehicle['model']} ({vehicle['year']})
Current Mileage: {vehicle['mileage']:,} miles

🔧 **SERVICE:**
Type: {service['type'].replace('_', ' ').title()}
{urgency_symbol} Urgency: {service['urgency'].upper()}
Description: {service['description']}
Estimated Duration: {apt_info['duration_estimate']}
Estimated Cost: {cost_display}

🏢 **SERVICE PROVIDER:**
{provider['name']} {"🏆 (Tier 1 Official)" if provider['tier'] == 1 else "⭐ (Tier 2 Specialist)"}
Location: {provider.get('location', 'TBC')} ({provider.get('distance_miles', 0):.1f} miles away)
Rating: {provider.get('rating', 0)}/5.0
Phone: {provider.get('phone', 'TBC')}

📅 **APPOINTMENT:**
Date: {formatted_date}
Time: {formatted_time}

👤 **CUSTOMER:**
Name: {customer['name']}
Phone: {customer['phone']}
Email: {customer['email']}

📋 **WHAT TO BRING:**
• Vehicle registration documents
• Service history book
• List of any additional concerns
• Payment method (card/cash accepted)

⏰ **IMPORTANT:**
• Please arrive 10 minutes early
• If running late, call {provider.get('phone', 'the provider')}
• To reschedule or cancel, contact us 24 hours in advance

📧 **CONFIRMATION SENT TO:** {customer['email']}

We'll send you a reminder 24 hours before your appointment.

Thank you for trusting Raava with your vehicle care! 🚗✨

[Replied by: Raava AI Service Manager]"""

        return message


# Singleton
service_appointment_manager = ServiceAppointmentManager()
