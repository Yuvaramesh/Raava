"""
Consignment Manager - Store vehicle listings in Consignments collection
"""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class ConsignmentManager:
    """Manages vehicle consignment listings"""

    LISTING_STATUSES = ["draft", "active", "sold", "expired", "withdrawn"]

    def __init__(self):
        self._consignments_col = None

    def _get_collection(self):
        """Lazy load Consignments collection"""
        if self._consignments_col is None:
            try:
                from database import db

                self._consignments_col = db["Consignments"]
            except Exception as e:
                print(f"❌ Could not load Consignments collection: {e}")
        return self._consignments_col

    def create_listing(
        self,
        vehicle_details: Dict[str, Any],
        service_history: Dict[str, Any],
        specifications: Dict[str, Any],
        condition_assessment: Dict[str, Any],
        asking_price: float,
        marketplaces: list,
        owner_contact: Dict[str, Any],
        valuation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create vehicle consignment listing

        Args:
            vehicle_details: {make, model, year, mileage}
            service_history: {description, full_history, recent_service}
            specifications: {engine_size, transmission, features}
            condition_assessment: {rating, notes}
            asking_price: Seller's asking price
            marketplaces: List of platforms to list on
            owner_contact: {name, email, phone}
            valuation: {trade_in, private_sale, retail}

        Returns:
            {success, listing_id, message}
        """
        try:
            listing_id = self._generate_listing_id()

            # Generate professional description
            description = self._generate_listing_description(
                vehicle_details,
                specifications,
                service_history,
                condition_assessment,
            )

            # Build listing document
            listing = {
                "listing_id": listing_id,
                "status": "active",
                # Vehicle information
                "vehicle": {
                    "make": vehicle_details.get("make", ""),
                    "model": vehicle_details.get("model", ""),
                    "year": vehicle_details.get("year"),
                    "mileage": vehicle_details.get("mileage", 0),
                    "registration": vehicle_details.get("registration", ""),
                },
                # Pricing
                "pricing": {
                    "asking_price": asking_price,
                    "valuation": valuation,
                    "negotiable": True,
                },
                # Specifications
                "specifications": {
                    "engine_size": specifications.get("engine_size", ""),
                    "transmission": specifications.get("transmission", ""),
                    "fuel_type": specifications.get("fuel_type", "Petrol"),
                    "body_type": specifications.get("body_type", "Coupe"),
                    "description": specifications.get("description", ""),
                },
                # Service & Condition
                "service_history": {
                    "full_history": service_history.get("full_history", False),
                    "recent_service": service_history.get("recent_service", False),
                    "description": service_history.get("description", ""),
                },
                "condition": {
                    "rating": condition_assessment.get("rating", 7),
                    "notes": condition_assessment.get("notes", ""),
                    "exterior": condition_assessment.get("exterior", "Good"),
                    "interior": condition_assessment.get("interior", "Good"),
                },
                # Listing content
                "listing": {
                    "title": f"{vehicle_details.get('year')} {vehicle_details.get('make')} {vehicle_details.get('model')}",
                    "description": description,
                    "highlights": self._generate_highlights(
                        vehicle_details, specifications, condition_assessment
                    ),
                },
                # Marketplaces
                "marketplaces": marketplaces,
                "marketplace_urls": {},  # Will be populated when published
                # Owner/Seller information
                "owner": {
                    "name": owner_contact.get("name", ""),
                    "email": owner_contact.get("email", ""),
                    "phone": owner_contact.get("phone", ""),
                },
                # Timestamps
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expires_at": self._calculate_expiry(),
                # Analytics
                "views": 0,
                "inquiries": 0,
                # Notes
                "internal_notes": [],
            }

            # Insert into Consignments collection
            col = self._get_collection()
            if col is None:
                return {"success": False, "message": "Database not available"}

            result = col.insert_one(listing)
            listing["_id"] = str(result.inserted_id)

            print(f"✅ LISTING SAVED TO CONSIGNMENTS COLLECTION")
            print(f"   Listing ID: {listing_id}")

            # Verify in database
            db_listing = col.find_one({"listing_id": listing_id})
            if db_listing:
                print(f"✅ VERIFIED IN CONSIGNMENTS COLLECTION")
            else:
                print(f"❌ NOT FOUND IN DATABASE!")

            # Generate confirmation message
            message = self._generate_confirmation_message(listing)

            return {
                "success": True,
                "listing_id": listing_id,
                "listing": listing,
                "message": message,
            }

        except Exception as e:
            print(f"❌ Error creating listing: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create listing. Please try again.",
            }

    def _generate_listing_id(self) -> str:
        """Generate unique listing ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique = str(uuid.uuid4())[:8].upper()
        return f"LST-RA-{timestamp[:4]}-{unique[:5]}"

    def _generate_listing_description(
        self,
        vehicle: Dict,
        specs: Dict,
        service: Dict,
        condition: Dict,
    ) -> str:
        """Generate professional listing description"""

        title = f"{vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}"

        description = f"**{title}**\n\n"

        # Opening paragraph
        description += f"Stunning {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')} "
        description += f"with just {vehicle.get('mileage', 0):,} miles on the clock. "
        description += (
            f"This exceptional example is presented in outstanding condition.\n\n"
        )

        # Key specifications
        description += "**Key Specifications:**\n"
        description += f"• Year: {vehicle.get('year')}\n"
        description += f"• Mileage: {vehicle.get('mileage', 0):,} miles\n"
        if specs.get("engine_size"):
            description += f"• Engine: {specs.get('engine_size')}\n"
        if specs.get("transmission"):
            description += f"• Transmission: {specs.get('transmission')}\n"
        description += "\n"

        # Service history
        description += "**Service History:**\n"
        if service.get("full_history"):
            description += "• Full main dealer service history\n"
        else:
            description += "• Service history available\n"
        if service.get("recent_service"):
            description += "• Recently serviced\n"
        description += "\n"

        # Condition
        description += "**Condition:**\n"
        description += f"• Overall rating: {condition.get('rating', 7)}/10\n"
        if condition.get("notes"):
            description += f"• {condition.get('notes')}\n"
        description += "\n"

        # Closing
        description += "This is a rare opportunity to own an exceptional example of this highly sought-after model. "
        description += "Viewing is highly recommended to fully appreciate the quality of this vehicle.\n\n"
        description += "Contact the owner to arrange a viewing or for more information."

        return description

    def _generate_highlights(self, vehicle: Dict, specs: Dict, condition: Dict) -> list:
        """Generate listing highlights"""
        highlights = []

        highlights.append(
            f"{vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}"
        )
        highlights.append(f"Only {vehicle.get('mileage', 0):,} miles")

        if condition.get("rating", 0) >= 8:
            highlights.append("Excellent condition")

        if specs.get("transmission"):
            highlights.append(f"{specs.get('transmission')} transmission")

        highlights.append("Ready to view")

        return highlights

    def _calculate_expiry(self) -> datetime:
        """Calculate listing expiry (90 days)"""
        from datetime import timedelta

        return datetime.utcnow() + timedelta(days=90)

    def _generate_confirmation_message(self, listing: Dict) -> str:
        """Generate confirmation message"""
        listing_id = listing["listing_id"]
        vehicle = listing["vehicle"]
        pricing = listing["pricing"]
        marketplaces = listing["marketplaces"]
        owner = listing["owner"]

        vehicle_title = f"{vehicle['make']} {vehicle['model']} ({vehicle['year']})"

        message = f"""✅ **LISTING CREATED SUCCESSFULLY**

**Listing ID:** {listing_id}

**Vehicle:** {vehicle_title}
**Mileage:** {vehicle['mileage']:,} miles
**Asking Price:** £{pricing['asking_price']:,}

**Listed On:**
{chr(10).join([f'• {mp}' for mp in marketplaces])}

**Seller Contact:** {owner['name']}
**Email:** {owner['email']}
**Phone:** {owner['phone']}

**Listing Details:**
{listing['listing']['description'][:500]}...

**Next Steps:**
1. Your listing is now LIVE on selected marketplaces
2. You'll receive email notifications for inquiries
3. Listing expires in 90 days (auto-renewable)
4. Update listing anytime by contacting us

**Professional Photography:**
We recommend adding professional photos to maximize interest.
Contact us to arrange a photography session.

**Marketing Package Available:**
• Featured listing placement
• Social media promotion
• Email newsletter feature
• Premium marketplace positioning

Thank you for choosing Raava Consignment! We'll help you sell your {vehicle['make']} quickly and at the best price! 📸✨

[Replied by: Raava AI Consigner]"""

        return message

    def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Get listing by ID"""
        try:
            col = self._get_collection()
            if col is None:
                return None

            listing = col.find_one({"listing_id": listing_id})
            if listing:
                listing["_id"] = str(listing["_id"])
            return listing
        except Exception as e:
            print(f"❌ Error retrieving listing: {e}")
            return None

    def update_listing_status(
        self, listing_id: str, status: str, note: Optional[str] = None
    ) -> bool:
        """Update listing status"""
        if status not in self.LISTING_STATUSES:
            return False

        try:
            col = self._get_collection()
            if col is None:
                return False

            update_data = {"status": status, "updated_at": datetime.utcnow()}

            if note:
                update_data["$push"] = {
                    "internal_notes": {
                        "timestamp": datetime.utcnow(),
                        "note": note,
                        "status": status,
                    }
                }

            result = col.update_one({"listing_id": listing_id}, {"$set": update_data})

            return result.modified_count > 0

        except Exception as e:
            print(f"❌ Error updating listing: {e}")
            return False

    def get_owner_listings(self, email: str, limit: int = 10) -> list:
        """Get all listings for an owner"""
        try:
            col = self._get_collection()
            if col is None:
                return []

            listings = (
                col.find({"owner.email": email}).sort("created_at", -1).limit(limit)
            )

            return [self._serialize_listing(lst) for lst in listings]
        except Exception as e:
            print(f"❌ Error retrieving listings: {e}")
            return []

    def _serialize_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        listing["_id"] = str(listing["_id"])

        # Convert datetime objects
        for field in ["created_at", "updated_at", "expires_at"]:
            if field in listing and isinstance(listing[field], datetime):
                listing[field] = listing[field].isoformat()

        return listing


# Singleton
consignment_manager = ConsignmentManager()
