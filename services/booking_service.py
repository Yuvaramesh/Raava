import os
from datetime import datetime
from pymongo import MongoClient
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class BookingService:
    """Handle car bookings and rentals with MongoDB storage"""

    def __init__(self):
        client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
        self.db = client["Raava_Sales"]
        self.orders_collection = self.db["Orders"]
        self.reservations_collection = self.db["Reservations"]

    def create_order(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new car purchase/rental order

        Expected fields:
        - car_id: Index of the car in Cars collection
        - car_title: Name of the car
        - first_name: Customer first name
        - last_name: Customer last name
        - email: Customer email
        - phone: Customer phone number
        - address: Full address
        - postcode: Postcode
        - booking_type: 'purchase' or 'rental'
        - rental_start_date: (for rentals) Start date
        - rental_end_date: (for rentals) End date
        - financing_option: PCP, HP, Personal Loan, or Cash
        - additional_notes: Any special requests
        """
        try:
            booking_data["created_at"] = datetime.utcnow()
            booking_data["status"] = "confirmed"
            booking_data["order_id"] = self._generate_order_id()

            result = self.orders_collection.insert_one(booking_data)

            return {
                "success": True,
                "order_id": booking_data["order_id"],
                "message": f"Booking confirmed! Your order ID is {booking_data['order_id']}",
            }
        except Exception as e:
            return {"success": False, "message": f"Error creating booking: {str(e)}"}

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an order by order ID"""
        try:
            return self.orders_collection.find_one({"order_id": order_id})
        except Exception as e:
            print(f"Error retrieving order: {str(e)}")
            return None

    def get_customer_orders(self, email: str) -> list:
        """Get all orders for a customer by email"""
        try:
            return list(self.orders_collection.find({"email": email}))
        except Exception as e:
            print(f"Error retrieving customer orders: {str(e)}")
            return []

    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status (e.g., 'pending', 'confirmed', 'completed')"""
        try:
            result = self.orders_collection.update_one(
                {"order_id": order_id},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}},
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating order: {str(e)}")
            return False

    def validate_booking_data(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate required booking fields"""
        required_fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "postcode",
            "car_title",
            "booking_type",
        ]

        missing_fields = [f for f in required_fields if not data.get(f)]

        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        # Email validation
        if "@" not in data.get("email", ""):
            return False, "Invalid email address"

        # Phone validation (basic)
        phone = data.get("phone", "").replace(" ", "")
        if not phone or len(phone) < 10:
            return False, "Invalid phone number"

        # For rentals, check dates
        if data.get("booking_type") == "rental":
            if not data.get("rental_start_date") or not data.get("rental_end_date"):
                return False, "Rental start and end dates are required"

        return True, "Valid"

    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        import uuid

        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"RAA-{timestamp}-{unique_id}"

    def get_booking_summary(self, booking_data: Dict[str, Any]) -> str:
        """Generate a human-readable booking summary"""
        summary = f"""
RAAVA BOOKING CONFIRMATION
{'=' * 40}

Order ID: {booking_data.get('order_id', 'N/A')}
Date: {datetime.utcnow().strftime('%d %b %Y, %H:%M')}

VEHICLE DETAILS:
{booking_data.get('car_title', 'N/A')}

CUSTOMER INFORMATION:
Name: {booking_data.get('first_name')} {booking_data.get('last_name')}
Email: {booking_data.get('email')}
Phone: {booking_data.get('phone')}
Address: {booking_data.get('address')}, {booking_data.get('postcode')}

BOOKING TYPE: {booking_data.get('booking_type', 'N/A').upper()}
"""

        if booking_data.get("booking_type") == "rental":
            summary += f"""
Rental Period: {booking_data.get('rental_start_date')} to {booking_data.get('rental_end_date')}
"""

        if booking_data.get("financing_option"):
            summary += f"""
Financing: {booking_data.get('financing_option')}
"""

        summary += f"""
Status: CONFIRMED ✓

A specialist will contact you within 24 hours to complete the details.
Thank you for choosing Raava!
"""
        return summary
