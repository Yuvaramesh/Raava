"""
Order Manager - PRODUCTION READY VERSION
Handles bookings, rentals, and purchases
Stores orders in Raava_Sales.Orders collection
Sends confirmation emails
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from bson import ObjectId
import uuid


class OrderManager:
    """Manages vehicle orders - PRODUCTION READY"""

    ORDER_TYPES = ["purchase", "rental", "booking"]
    ORDER_STATUSES = ["pending", "confirmed", "completed", "cancelled"]

    def __init__(self):
        self._orders_col = None
        self._cars_col = None
        self._users_col = None

    def _get_collections(self):
        """Lazy load collections to avoid import issues"""
        if self._orders_col is None:
            try:
                from database import orders_col, cars_col, users_col

                self._orders_col = orders_col
                self._cars_col = cars_col
                self._users_col = users_col
            except Exception as e:
                print(f"❌ Failed to load collections: {e}")
        return self._orders_col, self._cars_col, self._users_col

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
        try:
            orders_col, cars_col, users_col = self._get_collections()

            if orders_col is None:
                return {
                    "success": False,
                    "message": "Database not available",
                }

            # Generate unique order ID
            order_id = self._generate_order_id()

            print(f"\n{'='*70}")
            print(f"🔥 CREATING ORDER IN DATABASE")
            print(f"{'='*70}")
            print(f"Order ID: {order_id}")
            print(f"Order Type: {order_type}")
            print(f"Vehicle: {vehicle.get('make')} {vehicle.get('model')}")
            print(f"Customer: {customer.get('name')} ({customer.get('email')})")
            print(f"Payment: {'Finance' if finance_details else 'Cash'}")

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
                    "title": vehicle.get(
                        "title",
                        f"{vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('year')})",
                    ),
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
                    "type": finance_details.get("type", ""),
                    "provider": finance_details.get("provider", ""),
                    "monthly_payment": finance_details.get("monthly_payment", 0),
                    "deposit_amount": finance_details.get("deposit_amount", 0),
                    "term_months": finance_details.get("term_months", 48),
                    "apr": finance_details.get("apr", 0),
                    "total_cost": finance_details.get("total_cost", 0),
                    "balloon_payment": finance_details.get("balloon_payment", 0),
                }
                order["total_amount"] = finance_details.get(
                    "total_cost", vehicle.get("price", 0)
                )

                print(f"Finance Type: {finance_details.get('type')}")
                print(
                    f"Monthly Payment: £{finance_details.get('monthly_payment', 0):,.2f}"
                )
                print(f"Provider: {finance_details.get('provider')}")

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
                    "insurance_included": rental_details.get(
                        "insurance_included", True
                    ),
                    "delivery_required": rental_details.get("delivery_required", False),
                    "collection_address": rental_details.get("collection_address", ""),
                }
                order["total_amount"] = order["rental"]["total_rental_cost"]

            elif order_type == "booking":
                booking_date = customer.get(
                    "preferred_date", datetime.utcnow() + timedelta(days=1)
                )

                if isinstance(booking_date, str):
                    booking_date = datetime.fromisoformat(booking_date)

                order["booking"] = {
                    "type": customer.get("booking_type", "viewing"),
                    "preferred_date": booking_date,
                    "preferred_time": customer.get("preferred_time", "10:00"),
                    "duration_minutes": customer.get("duration_minutes", 60),
                    "location": customer.get("location", "Dealer Location"),
                    "special_requests": customer.get("special_requests", ""),
                }
                order["total_amount"] = 0

            else:
                order["total_amount"] = vehicle.get("price", 0)

            print(f"Total Amount: £{order['total_amount']:,}")

            # Insert into database
            print(f"\n💾 Inserting order into Orders collection...")

            result = orders_col.insert_one(order)
            order["_id"] = str(result.inserted_id)

            print(f"✅ Database insert successful")
            print(f"   MongoDB _id: {result.inserted_id}")
            print(f"   Order ID: {order_id}")

            # Verify the order was saved
            print(f"\n🔍 Verifying order in database...")
            verification = orders_col.find_one({"order_id": order_id})

            if verification:
                print(f"✅ VERIFICATION SUCCESSFUL")
                print(f"   Order {order_id} found in Orders collection")
                print(f"   Customer: {verification.get('customer', {}).get('email')}")
                print(f"   Vehicle: {verification.get('vehicle', {}).get('title')}")
                print(f"   Status: {verification.get('status')}")
            else:
                print(f"❌ VERIFICATION FAILED")
                print(f"   Order {order_id} NOT found in database!")

            # Update user record (FIXED: proper None check)
            if customer.get("email") and users_col is not None:
                self._update_user_orders(customer["email"], order_id, users_col)

            # Send confirmation email
            print(f"\n📧 Sending confirmation email...")
            email_sent = self._send_order_confirmation_email(order)

            if email_sent:
                print(f"✅ Confirmation email sent to {customer.get('email')}")
            else:
                print(f"⚠️  Email not sent (check SMTP configuration)")

            # Generate confirmation message
            message = self._generate_order_confirmation_message(order)

            print(f"\n{'='*70}")
            print(f"✅ ORDER CREATION COMPLETE")
            print(f"{'='*70}\n")

            return {
                "success": True,
                "order_id": order_id,
                "order": order,
                "message": message,
                "email_sent": email_sent,
            }

        except Exception as e:
            print(f"\n❌ EXCEPTION IN ORDER CREATION:")
            print(f"   Error: {e}")
            import traceback

            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create order. Please try again.",
            }

    def _send_order_confirmation_email(self, order: Dict[str, Any]) -> bool:
        """Send order confirmation email"""
        try:
            from enhanced_email_service import enhanced_email_service

            customer_email = order.get("customer", {}).get("email")
            if not customer_email:
                print("⚠️  No customer email provided")
                return False

            print(f"   Recipient: {customer_email}")
            print(f"   Order ID: {order.get('order_id')}")

            result = enhanced_email_service.send_order_confirmation(order)

            return result

        except Exception as e:
            print(f"❌ Email sending error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve order by order_id"""
        try:
            orders_col, _, _ = self._get_collections()
            if orders_col is None:
                return None

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
            orders_col, _, _ = self._get_collections()
            if orders_col is None:
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
            orders_col, _, _ = self._get_collections()
            if orders_col is None:
                return []

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

    def _update_user_orders(self, email: str, order_id: str, users_col):
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

        vehicle_title = vehicle["title"]

        if order_type == "purchase":
            if "finance" in order:
                finance = order["finance"]
                msg = f"""✅ **PURCHASE ORDER CONFIRMED**

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
**Email:** {customer['email']}
**Phone:** {customer['phone']}

**Next Steps:**
1. Confirmation email sent to {customer['email']}
2. Finance application processing (24-48 hours)
3. Our team will contact you to arrange delivery
4. Vehicle preparation: 3-5 working days

Thank you for choosing Raava! Your luxury automotive experience begins now! 🚗✨

[Replied by: Raava AI Concierge]"""
            else:
                msg = f"""✅ **PURCHASE ORDER CONFIRMED**

**Order ID:** {order_id}

**Vehicle:** {vehicle_title}
**Total Amount:** £{order['total_amount']:,}

**Customer:** {customer['name']}
**Email:** {customer['email']}
**Phone:** {customer['phone']}

**Next Steps:**
1. Confirmation email sent to {customer['email']}
2. Payment instructions will be sent separately
3. Delivery scheduled within 7 working days
4. All documentation prepared

We look forward to delivering your {vehicle['make']} {vehicle['model']}!

[Replied by: Raava AI Concierge]"""

            return msg

        return f"Order {order_id} created successfully"


# Singleton instance
order_manager = OrderManager()
