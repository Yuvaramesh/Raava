"""
Order Manager - Handle bookings, rentals, and purchases
Stores orders in Raava_Sales.Orders collection
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from bson import ObjectId
import uuid

from db_schema_manager import orders_col, cars_col, users_col
from config import LUXURY_MAKES


class OrderManager:
    """Manages vehicle orders (bookings, rentals, purchases)"""

    ORDER_TYPES = ["purchase", "rental", "booking"]
    ORDER_STATUSES = ["pending", "confirmed", "completed", "cancelled"]

    def create_order(
        self,
        order_type: str,
        vehicle: Dict[str, Any],
        customer: Dict[str, Any],
        finance_details: Optional[Dict[str, Any]] = None,
        rental_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new order in the Orders collection

        Args:
            order_type: "purchase", "rental", or "booking"
            vehicle: Vehicle details from Cars collection
            customer: Customer information
            finance_details: Finance option selected (for purchases)
            rental_details: Rental period and terms (for rentals)

        Returns:
            Order document with order_id
        """
        # Generate unique order ID
        order_id = self._generate_order_id()

        # Prepare order document
        order = {
            "order_id": order_id,
            "order_type": order_type,
            "status": "pending",
            # Vehicle information
            "vehicle": {
                "vehicle_id": str(vehicle.get("_id", "")),
                "make": vehicle.get("make", ""),
                "model": vehicle.get("model", ""),
                "year": vehicle.get("year", ""),
                "price": vehicle.get("price", 0),
                "mileage": vehicle.get("mileage", 0),
                "fuel_type": vehicle.get("fuel_type", ""),
                "body_type": vehicle.get("body_type", vehicle.get("style", "")),
                "description": vehicle.get("description", ""),
                "images": vehicle.get("images", []),
                "source": vehicle.get("source", "Raava Exclusive"),
                "listing_url": vehicle.get("url", ""),
            },
            # Customer information
            "customer": {
                "name": customer.get("name", ""),
                "email": customer.get("email", ""),
                "phone": customer.get("phone", ""),
                "address": customer.get("address", ""),
                "postcode": customer.get("postcode", ""),
            },
            # Timestamps
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            # Session tracking
            "session_id": customer.get("session_id", ""),
            # Notes
            "notes": [],
            "internal_notes": [],
        }

        # Add finance details for purchases
        if order_type == "purchase" and finance_details:
            order["finance"] = {
                "type": finance_details.get("type", ""),  # PCP, HP, Lease
                "provider": finance_details.get("provider", ""),
                "monthly_payment": finance_details.get("monthly_payment", 0),
                "deposit_amount": finance_details.get("deposit_amount", 0),
                "term_months": finance_details.get("term_months", 48),
                "apr": finance_details.get("apr", 0),
                "total_cost": finance_details.get("total_cost", 0),
                "balloon_payment": finance_details.get("balloon_payment", 0),
            }

            # Calculate total order value
            order["total_amount"] = finance_details.get(
                "total_cost", vehicle.get("price", 0)
            )

        # Add rental details for rentals
        elif order_type == "rental" and rental_details:
            start_date = rental_details.get("start_date", datetime.utcnow())
            duration_days = rental_details.get("duration_days", 7)

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)

            end_date = start_date + timedelta(days=duration_days)

            order["rental"] = {
                "start_date": start_date,
                "end_date": end_date,
                "duration_days": duration_days,
                "daily_rate": rental_details.get("daily_rate", 0),
                "total_rental_cost": rental_details.get("daily_rate", 0)
                * duration_days,
                "deposit_required": rental_details.get("deposit_required", 0),
                "mileage_limit": rental_details.get("mileage_limit", 150)
                * duration_days,
                "insurance_included": rental_details.get("insurance_included", True),
                "delivery_required": rental_details.get("delivery_required", False),
                "collection_address": rental_details.get("collection_address", ""),
            }

            order["total_amount"] = order["rental"]["total_rental_cost"]

        # For simple bookings (viewing/test drive)
        elif order_type == "booking":
            booking_date = customer.get(
                "preferred_date", datetime.utcnow() + timedelta(days=1)
            )

            if isinstance(booking_date, str):
                booking_date = datetime.fromisoformat(booking_date)

            order["booking"] = {
                "type": customer.get("booking_type", "viewing"),  # viewing, test_drive
                "preferred_date": booking_date,
                "preferred_time": customer.get("preferred_time", "10:00"),
                "duration_minutes": customer.get("duration_minutes", 60),
                "location": customer.get("location", "Dealer Location"),
                "special_requests": customer.get("special_requests", ""),
            }

            order["total_amount"] = 0  # Bookings are free

        else:
            # Default purchase without finance
            order["total_amount"] = vehicle.get("price", 0)

        # Insert into database
        try:
            result = orders_col.insert_one(order)
            order["_id"] = str(result.inserted_id)

            # Update user record
            if customer.get("email"):
                self._update_user_orders(customer["email"], order_id)

            return {
                "success": True,
                "order_id": order_id,
                "order": order,
                "message": self._generate_order_confirmation_message(order),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create order. Please try again.",
            }

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve order by order_id"""
        try:
            order = orders_col.find_one({"order_id": order_id})
            if order:
                order["_id"] = str(order["_id"])
            return order
        except Exception as e:
            print(f"Error retrieving order: {e}")
            return None

    def update_order_status(
        self, order_id: str, status: str, note: Optional[str] = None
    ) -> bool:
        """Update order status"""
        if status not in self.ORDER_STATUSES:
            return False

        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}

            if note:
                update_data["$push"] = {
                    "notes": {
                        "timestamp": datetime.utcnow(),
                        "note": note,
                        "status": status,
                    }
                }

            result = orders_col.update_one(
                {"order_id": order_id}, {"$set": update_data}
            )

            return result.modified_count > 0

        except Exception as e:
            print(f"Error updating order status: {e}")
            return False

    def get_customer_orders(self, email: str, limit: int = 10) -> list:
        """Get all orders for a customer"""
        try:
            orders = (
                orders_col.find({"customer.email": email})
                .sort("created_at", -1)
                .limit(limit)
            )

            return [self._serialize_order(order) for order in orders]
        except Exception as e:
            print(f"Error retrieving customer orders: {e}")
            return []

    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique = str(uuid.uuid4())[:8].upper()
        return f"ORD-RA-{timestamp[:4]}-{unique[:5]}"

    def _update_user_orders(self, email: str, order_id: str):
        """Update user document with new order"""
        try:
            users_col.update_one(
                {"email": email},
                {
                    "$push": {"orders": order_id},
                    "$set": {
                        "last_order_id": order_id,
                        "updated_at": datetime.utcnow(),
                    },
                },
                upsert=True,
            )
        except Exception as e:
            print(f"Error updating user orders: {e}")

    def _serialize_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Convert order to JSON-serializable format"""
        order["_id"] = str(order["_id"])

        # Convert datetime objects
        for field in ["created_at", "updated_at"]:
            if field in order and isinstance(order[field], datetime):
                order[field] = order[field].isoformat()

        # Convert rental dates
        if "rental" in order:
            for field in ["start_date", "end_date"]:
                if field in order["rental"] and isinstance(
                    order["rental"][field], datetime
                ):
                    order["rental"][field] = order["rental"][field].isoformat()

        # Convert booking date
        if "booking" in order and "preferred_date" in order["booking"]:
            if isinstance(order["booking"]["preferred_date"], datetime):
                order["booking"]["preferred_date"] = order["booking"][
                    "preferred_date"
                ].isoformat()

        return order

    def _generate_order_confirmation_message(self, order: Dict[str, Any]) -> str:
        """Generate confirmation message based on order type"""
        order_type = order["order_type"]
        order_id = order["order_id"]
        vehicle = order["vehicle"]
        customer = order["customer"]

        vehicle_title = f"{vehicle['make']} {vehicle['model']} ({vehicle['year']})"

        if order_type == "purchase":
            if "finance" in order:
                finance = order["finance"]
                msg = f"""✅ **ORDER CONFIRMED**

**Order ID:** {order_id}

**Vehicle:** {vehicle_title}
**Price:** £{vehicle['price']:,}

**Finance Details:**
• Type: {finance['type']}
• Provider: {finance['provider']}
• Monthly Payment: £{finance['monthly_payment']:,.2f}
• Term: {finance['term_months']} months
• Deposit: £{finance['deposit_amount']:,.2f}
• APR: {finance['apr']}%

**Customer:** {customer['name']}
**Delivery Address:** {customer['address']}

**Next Steps:**
1. You'll receive a confirmation email within 15 minutes
2. Finance application will be processed within 24 hours
3. Our team will contact you to arrange delivery
4. Vehicle preparation: 3-5 working days

**Payment:** Secure payment link will be sent via email

Thank you for choosing Raava. Your luxury automotive experience begins now! 🚗✨

[Replied by: Raava AI Concierge]"""
            else:
                msg = f"""✅ **PURCHASE ORDER CONFIRMED**

**Order ID:** {order_id}

**Vehicle:** {vehicle_title}
**Total Amount:** £{order['total_amount']:,}

**Customer:** {customer['name']}
**Delivery Address:** {customer['address']}

**Next Steps:**
1. Payment instructions sent to {customer['email']}
2. Delivery scheduled within 7 working days
3. All documentation prepared

We look forward to delivering your {vehicle['make']} {vehicle['model']}!

[Replied by: Raava AI Concierge]"""

        elif order_type == "rental":
            rental = order["rental"]
            msg = f"""✅ **RENTAL BOOKING CONFIRMED**

**Order ID:** {order_id}

**Vehicle:** {vehicle_title}
**Daily Rate:** £{rental['daily_rate']:,}

**Rental Period:**
• Start: {rental['start_date'].strftime('%d %B %Y')}
• End: {rental['end_date'].strftime('%d %B %Y')}
• Duration: {rental['duration_days']} days
• Total Cost: £{rental['total_rental_cost']:,}

**Mileage Limit:** {rental['mileage_limit']} miles
**Insurance:** {'Included' if rental['insurance_included'] else 'Not Included'}
**Deposit Required:** £{rental['deposit_required']:,}

**Customer:** {customer['name']}
**Collection:** {rental['collection_address'] or 'To be confirmed'}

**Next Steps:**
1. Payment link sent to {customer['email']}
2. Collection details confirmed 24 hours before
3. Vehicle preparation completed

Enjoy your luxury driving experience! 🚗✨

[Replied by: Raava AI Concierge]"""

        elif order_type == "booking":
            booking = order["booking"]
            booking_type = (
                "Test Drive" if booking["type"] == "test_drive" else "Viewing"
            )
            msg = f"""✅ **{booking_type.upper()} CONFIRMED**

**Booking ID:** {order_id}

**Vehicle:** {vehicle_title}

**Appointment Details:**
• Date: {booking['preferred_date'].strftime('%d %B %Y')}
• Time: {booking['preferred_time']}
• Duration: {booking['duration_minutes']} minutes
• Location: {booking['location']}

**Customer:** {customer['name']}
**Contact:** {customer['phone']}

{f"**Special Requests:** {booking['special_requests']}" if booking['special_requests'] else ""}

**What to Bring:**
• Valid UK driving licence (for test drives)
• Proof of address
• Photo ID

**Confirmation sent to:** {customer['email']}

We look forward to welcoming you! If you need to reschedule, please contact us 24 hours in advance.

[Replied by: Raava AI Concierge]"""

        else:
            msg = f"""✅ **ORDER CONFIRMED**

**Order ID:** {order_id}
**Vehicle:** {vehicle_title}

Your order has been received and is being processed.
Our team will contact you shortly at {customer['email']}.

[Replied by: Raava AI Concierge]"""

        return msg


# Singleton instance
order_manager = OrderManager()
