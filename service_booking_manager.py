"""
Service Booking Manager - FIXED VERSION
Store appointments in Services collection and send confirmation emails
"""

from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
import uuid


class ServiceBookingManager:
    """Manages service appointments in Services collection"""

    APPOINTMENT_STATUSES = [
        "pending",
        "confirmed",
        "in_progress",
        "completed",
        "cancelled",
    ]

    def __init__(self):
        self._services_col = None

    def _get_collection(self):
        """Lazy load Services collection"""
        if self._services_col is None:
            try:
                from database import db

                if db is not None:
                    self._services_col = db["Services"]
                    print("✅ Services collection loaded")
                else:
                    print("❌ Database not available")
            except Exception as e:
                print(f"❌ Could not load Services collection: {e}")
        return self._services_col

    def create_service_appointment(
        self,
        vehicle_info: Dict[str, Any],
        service_request: Dict[str, Any],
        customer_info: Dict[str, Any],
        provider_info: Dict[str, Any],
        appointment_datetime: datetime,
    ) -> Dict[str, Any]:
        """
        Create service appointment in Services collection

        Args:
            vehicle_info: {make, model, year, mileage}
            service_request: {type, description, urgency}
            customer_info: {name, email, phone, postcode}
            provider_info: {name, location, phone, estimated_cost, rating, distance_miles}
            appointment_datetime: datetime object

        Returns:
            {success, appointment_id, message}
        """
        try:
            print("\n" + "=" * 70)
            print("📅 CREATING SERVICE APPOINTMENT")
            print("=" * 70)

            # Generate appointment ID
            appointment_id = self._generate_appointment_id()
            print(f"\n📋 Appointment ID: {appointment_id}")

            # Get collection
            col = self._get_collection()
            if col is None:
                print("❌ Services collection not available")
                return {
                    "success": False,
                    "message": "Database not available",
                }

            # Build appointment document
            appointment = {
                "appointment_id": appointment_id,
                "status": "pending",
                # Vehicle information
                "vehicle": {
                    "make": vehicle_info.get("make", ""),
                    "model": vehicle_info.get("model", ""),
                    "year": vehicle_info.get("year"),
                    "mileage": vehicle_info.get("mileage", 0),
                },
                # Service details
                "service": {
                    "type": service_request.get("type", "general_service"),
                    "description": service_request.get("description", ""),
                    "urgency": service_request.get("urgency", "routine"),
                },
                # Customer information
                "customer": {
                    "name": customer_info.get("name", ""),
                    "email": customer_info.get("email", ""),
                    "phone": customer_info.get("phone", ""),
                    "postcode": customer_info.get("postcode", ""),
                },
                # Service provider
                "provider": {
                    "name": provider_info.get("name", ""),
                    "location": provider_info.get("location", ""),
                    "phone": provider_info.get("phone", ""),
                    "estimated_cost": provider_info.get("estimated_cost", 0),
                    "rating": provider_info.get("rating", 0),
                    "distance_miles": provider_info.get("distance_miles", 0),
                },
                # Appointment scheduling
                "appointment": {
                    "datetime": appointment_datetime,
                    "formatted": appointment_datetime.strftime(
                        "%A, %d %B %Y at %I:%M %p"
                    ),
                },
                # Timestamps
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                # Session tracking
                "session_id": customer_info.get("session_id", ""),
                # Notes
                "notes": [],
                "internal_notes": [],
            }

            # Debug print
            print(f"\n📊 Appointment Data:")
            print(
                f"   Vehicle: {appointment['vehicle']['make']} {appointment['vehicle']['model']}"
            )
            print(
                f"   Customer: {appointment['customer']['name']} - {appointment['customer']['email']}"
            )
            print(f"   Provider: {appointment['provider']['name']}")
            print(f"   Date: {appointment['appointment']['formatted']}")

            # Insert into Services collection
            print(f"\n💾 Inserting into Services collection...")
            result = col.insert_one(appointment)
            appointment["_id"] = str(result.inserted_id)

            print(f"✅ INSERTED TO DATABASE")
            print(f"   MongoDB _id: {result.inserted_id}")
            print(f"   Appointment ID: {appointment_id}")

            # Verify it's in database
            print(f"\n🔍 Verifying in database...")
            db_appointment = col.find_one({"appointment_id": appointment_id})

            if db_appointment:
                print(f"✅ VERIFIED IN SERVICES COLLECTION")
                print(f"   Customer: {db_appointment.get('customer', {}).get('email')}")
                print(f"   Status: {db_appointment.get('status')}")
            else:
                print(f"❌ NOT FOUND IN DATABASE!")
                return {
                    "success": False,
                    "message": "Failed to verify appointment in database",
                }

            # Send confirmation email
            print(f"\n📧 Sending confirmation email...")
            email_sent = self._send_appointment_confirmation(appointment)

            if email_sent:
                print(f"✅ EMAIL SENT to {appointment['customer']['email']}")
            else:
                print(f"⚠️ EMAIL NOT SENT (check SMTP configuration)")

            # Generate confirmation message
            message = self._generate_confirmation_message(appointment)

            print(f"\n" + "=" * 70)
            print(f"✅ APPOINTMENT CREATION COMPLETE")
            print(f"=" * 70 + "\n")

            return {
                "success": True,
                "appointment_id": appointment_id,
                "appointment": appointment,
                "message": message,
                "email_sent": email_sent,
            }

        except Exception as e:
            print(f"\n❌ EXCEPTION IN APPOINTMENT CREATION:")
            print(f"   Error: {e}")
            import traceback

            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create appointment. Please try again.",
            }

    def get_appointment(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment by ID"""
        try:
            col = self._get_collection()
            if col is None:
                return None

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
        if status not in self.APPOINTMENT_STATUSES:
            return False

        try:
            col = self._get_collection()
            if col is None:
                return False

            update_data = {"status": status, "updated_at": datetime.utcnow()}

            if note:
                update_data["$push"] = {
                    "notes": {
                        "timestamp": datetime.utcnow(),
                        "note": note,
                        "status": status,
                    }
                }

            result = col.update_one(
                {"appointment_id": appointment_id}, {"$set": update_data}
            )

            return result.modified_count > 0

        except Exception as e:
            print(f"❌ Error updating appointment: {e}")
            return False

    def get_customer_appointments(self, email: str, limit: int = 10) -> list:
        """Get all appointments for a customer"""
        try:
            col = self._get_collection()
            if col is None:
                return []

            appointments = (
                col.find({"customer.email": email}).sort("created_at", -1).limit(limit)
            )

            return [self._serialize_appointment(apt) for apt in appointments]
        except Exception as e:
            print(f"❌ Error retrieving appointments: {e}")
            return []

    def _generate_appointment_id(self) -> str:
        """Generate unique appointment ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique = str(uuid.uuid4())[:8].upper()
        appointment_id = f"SVC-RA-{timestamp[:4]}-{unique[:5]}"
        print(f"📋 Generated ID: {appointment_id}")
        return appointment_id

    def _send_appointment_confirmation(self, appointment: Dict[str, Any]) -> bool:
        """Send confirmation email"""
        try:
            print("\n📧 Attempting to send email...")

            from enhanced_email_service import enhanced_email_service

            customer_email = appointment.get("customer", {}).get("email")
            if not customer_email:
                print("⚠️ No customer email provided")
                return False

            print(f"   Recipient: {customer_email}")
            print(f"   Appointment ID: {appointment.get('appointment_id')}")

            # Send using the service appointment email method
            result = enhanced_email_service.send_service_appointment_confirmation(
                appointment
            )

            if result:
                print(f"✅ Email sent successfully")
            else:
                print(f"❌ Email sending failed")

            return result

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _generate_confirmation_message(self, appointment: Dict[str, Any]) -> str:
        """Generate confirmation message"""
        appointment_id = appointment["appointment_id"]
        vehicle = appointment["vehicle"]
        service = appointment["service"]
        customer = appointment["customer"]
        provider = appointment["provider"]
        apt = appointment["appointment"]

        vehicle_title = f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"

        message = f"""✅ **SERVICE APPOINTMENT CONFIRMED**

**Appointment ID:** {appointment_id}

**Vehicle:** {vehicle_title}
**Mileage:** {vehicle['mileage']:,} miles

**Service Type:** {service['type'].replace('_', ' ').title()}
**Description:** {service['description']}

**Service Provider:** {provider['name']}
**Location:** {provider['location']}
**Phone:** {provider['phone']}
**Estimated Cost:** £{provider['estimated_cost']:,}

**Appointment:** {apt['formatted']}

**Customer:** {customer['name']}
**Contact:** {customer['email']} | {customer['phone']}

**Next Steps:**
1. Confirmation email sent to {customer['email']}
2. {provider['name']} will call you 24 hours before
3. Bring your vehicle service book
4. Allow 2-4 hours for service completion

**Need to reschedule?** Call {provider['phone']} at least 24 hours in advance.

Thank you for choosing Raava Service! We'll take excellent care of your {vehicle['make']}! 🔧✨

[Replied by: Raava AI Service Manager]"""

        return message

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


# Singleton
service_booking_manager = ServiceBookingManager()


# Test function to verify it works
if __name__ == "__main__":
    print("\n🧪 TESTING SERVICE BOOKING MANAGER")
    print("=" * 70)

    test_result = service_booking_manager.create_service_appointment(
        vehicle_info={
            "make": "Lamborghini",
            "model": "Huracan",
            "year": 2021,
            "mileage": 5000,
        },
        service_request={
            "type": "scheduled_service",
            "description": "Annual service",
            "urgency": "routine",
        },
        customer_info={
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+44 123 456 7890",
            "postcode": "SW1A 1AA",
        },
        provider_info={
            "name": "Test Garage",
            "location": "London",
            "phone": "020 1234 5678",
            "estimated_cost": 500,
            "rating": 4.8,
            "distance_miles": 5.0,
        },
        appointment_datetime=datetime(2026, 2, 1, 10, 0),
    )

    print(f"\n🧪 Test Result: {test_result.get('success')}")
    if test_result.get("success"):
        print(f"✅ Appointment ID: {test_result.get('appointment_id')}")
    else:
        print(f"❌ Error: {test_result.get('message')}")
