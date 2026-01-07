"""
Raava Database Seeder
Populate MongoDB with luxury car listings from your scraped data
"""

import sys

sys.path.append("..")

from pymongo import MongoClient
from config import MONGO_CONNECTION_STRING, LUXURY_MAKES
import json
from datetime import datetime


# Sample luxury cars to seed database (UK market)
SEED_DATA = [
    {
        "make": "Ferrari",
        "model": "488 GTB",
        "year": 2017,
        "price": 189950,
        "mileage": 8400,
        "fuel_type": "Petrol",
        "body_type": "Coupe",
        "style": "Coupe",
        "engine": "3.9L V8 Twin-Turbo",
        "power": "660 HP",
        "description": "Rosso Corsa over Nero leather. Full Ferrari service history. UK supplied car with only 8,400 miles. Immaculate condition.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/ferrari-488-gtb-1.jpg"],
        "url": "https://www.autotrader.co.uk/car-details/ferrari-488",
        "source": "AutoTrader",
        "location": "London",
        "seller_type": "Dealer",
        "seller_name": "H.R. Owen London",
        "postcode": "SW1A 1AA",
    },
    {
        "make": "Porsche",
        "model": "911 Turbo S",
        "year": 2020,
        "price": 149950,
        "mileage": 5200,
        "fuel_type": "Petrol",
        "body_type": "Coupe",
        "style": "Coupe",
        "engine": "3.8L Flat-6 Twin-Turbo",
        "power": "640 HP",
        "description": "GT Silver Metallic. Full Porsche main dealer service history. Sport Chrono, PDCC, Burmester audio. One owner from new.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/porsche-911-turbo-s.jpg"],
        "url": "https://www.autotrader.co.uk/car-details/porsche-911",
        "source": "Raava Exclusive",
        "location": "Manchester",
        "seller_type": "Dealer",
        "seller_name": "Porsche Centre Manchester",
        "postcode": "M1 1AA",
    },
    {
        "make": "Lamborghini",
        "model": "Huracán EVO",
        "year": 2021,
        "price": 219950,
        "mileage": 2800,
        "fuel_type": "Petrol",
        "body_type": "Coupe",
        "style": "Coupe",
        "engine": "5.2L V10",
        "power": "640 HP",
        "description": "Grigio Titans over Nero Ade. Just 2,800 miles. Full Lamborghini service history. Lifting system, carbon interior package.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/lamborghini-huracan-evo.jpg"],
        "url": "https://www.pistonheads.com/classifieds/used-cars/lamborghini",
        "source": "PistonHeads",
        "location": "Surrey",
        "seller_type": "Dealer",
        "seller_name": "H.R. Owen Lamborghini",
        "postcode": "KT1 1AA",
    },
    {
        "make": "Aston Martin",
        "model": "DB11 V12",
        "year": 2019,
        "price": 124950,
        "mileage": 12000,
        "fuel_type": "Petrol",
        "body_type": "Coupe",
        "style": "Coupe",
        "engine": "5.2L V12 Twin-Turbo",
        "power": "608 HP",
        "description": "Midnight Blue over Obsidian Black leather. Full Aston Martin service history. Sports Plus pack, Bang & Olufsen audio.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/aston-martin-db11.jpg"],
        "url": "https://www.cargurus.co.uk/Cars/aston-martin-db11",
        "source": "CarGurus",
        "location": "Birmingham",
        "seller_type": "Dealer",
        "seller_name": "Aston Martin Birmingham",
        "postcode": "B1 1AA",
    },
    {
        "make": "McLaren",
        "model": "720S",
        "year": 2018,
        "price": 179950,
        "mileage": 6500,
        "fuel_type": "Petrol",
        "body_type": "Coupe",
        "style": "Coupe",
        "engine": "4.0L V8 Twin-Turbo",
        "power": "710 HP",
        "description": "Volcano Orange. McLaren approved with full service history. Sport Exhaust, Stealth Pack, Bowers & Wilkins audio. Track telemetry.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/mclaren-720s.jpg"],
        "url": "https://www.motors.co.uk/car-details/mclaren-720s",
        "source": "Motors.co.uk",
        "location": "Leeds",
        "seller_type": "Dealer",
        "seller_name": "Stratstone McLaren Leeds",
        "postcode": "LS1 1AA",
    },
    {
        "make": "Bentley",
        "model": "Continental GT",
        "year": 2020,
        "price": 139950,
        "mileage": 8900,
        "fuel_type": "Petrol",
        "body_type": "Coupe",
        "style": "Coupe",
        "engine": "6.0L W12 Twin-Turbo",
        "power": "626 HP",
        "description": "Beluga Black over Hotspur leather. Mulliner Driving Specification. Full Bentley service history. Rotating display, Naim audio.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/bentley-continental-gt.jpg"],
        "url": "https://www.autotrader.co.uk/car-details/bentley-continental",
        "source": "AutoTrader",
        "location": "Edinburgh",
        "seller_type": "Dealer",
        "seller_name": "Bentley Edinburgh",
        "postcode": "EH1 1AA",
    },
    {
        "make": "Mercedes-AMG",
        "model": "GT R",
        "year": 2019,
        "price": 119950,
        "mileage": 9200,
        "fuel_type": "Petrol",
        "body_type": "Coupe",
        "style": "Coupe",
        "engine": "4.0L V8 Twin-Turbo",
        "power": "577 HP",
        "description": "AMG Green Hell Magno. Full Mercedes-Benz service history. Carbon fibre package, AMG track pace, Burmester audio.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/mercedes-amg-gt-r.jpg"],
        "url": "https://www.autotrader.co.uk/car-details/mercedes-amg-gt-r",
        "source": "Raava Exclusive",
        "location": "Bristol",
        "seller_type": "Dealer",
        "seller_name": "Mercedes-Benz of Bristol",
        "postcode": "BS1 1AA",
    },
    {
        "make": "Rolls-Royce",
        "model": "Ghost",
        "year": 2021,
        "price": 249950,
        "mileage": 3500,
        "fuel_type": "Petrol",
        "body_type": "Saloon",
        "style": "Saloon",
        "engine": "6.75L V12 Twin-Turbo",
        "power": "563 HP",
        "description": "Arctic White over Navy leather. Extended wheelbase. Starlight headliner, lambswool floor mats, refrigerated compartment.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/rolls-royce-ghost.jpg"],
        "url": "https://www.pistonheads.com/classifieds/rolls-royce-ghost",
        "source": "PistonHeads",
        "location": "London",
        "seller_type": "Dealer",
        "seller_name": "H.R. Owen Rolls-Royce",
        "postcode": "W1A 1AA",
    },
    {
        "make": "Porsche",
        "model": "Taycan Turbo S",
        "year": 2022,
        "price": 124950,
        "mileage": 4100,
        "fuel_type": "Electric",
        "body_type": "Saloon",
        "style": "Saloon",
        "engine": "Electric Dual-Motor",
        "power": "761 HP",
        "range_miles": 280,
        "description": "Frozen Blue Metallic. Full Porsche service history. Sport Chrono, PASM, rear-axle steering, premium audio.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/porsche-taycan-turbo-s.jpg"],
        "url": "https://www.cargurus.co.uk/Cars/porsche-taycan",
        "source": "CarGurus",
        "location": "Cambridge",
        "seller_type": "Dealer",
        "seller_name": "Porsche Centre Cambridge",
        "postcode": "CB1 1AA",
    },
    {
        "make": "BMW M",
        "model": "M8 Competition",
        "year": 2021,
        "price": 89950,
        "mileage": 7800,
        "fuel_type": "Petrol",
        "body_type": "Coupe",
        "style": "Coupe",
        "engine": "4.4L V8 Twin-Turbo",
        "power": "625 HP",
        "description": "Frozen Marina Bay Blue. BMW Individual specification. Carbon ceramics, M Driver's Package, Merino leather.",
        "images": ["https://m.atcdn.co.uk/a/media/w800/bmw-m8-competition.jpg"],
        "url": "https://www.motors.co.uk/car-details/bmw-m8",
        "source": "Motors.co.uk",
        "location": "Oxford",
        "seller_type": "Dealer",
        "seller_name": "BMW Oxford",
        "postcode": "OX1 1AA",
    },
]


def seed_database():
    """Seed MongoDB with luxury car data"""
    try:
        print("🚗 Raava Database Seeder")
        print("=" * 60)

        # Connect to MongoDB
        print(f"Connecting to MongoDB...")
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client["Raava_Sales"]
        cars_collection = db["Cars"]

        print(f"✓ Connected to database: {db.name}")

        # Clear existing data (optional)
        existing_count = cars_collection.count_documents({})
        if existing_count > 0:
            response = input(
                f"\n⚠️  Database has {existing_count} cars. Clear existing data? (y/N): "
            )
            if response.lower() == "y":
                cars_collection.delete_many({})
                print(f"✓ Cleared {existing_count} existing records")

        # Insert seed data
        print(f"\n📥 Inserting {len(SEED_DATA)} luxury vehicles...")

        for i, car in enumerate(SEED_DATA, 1):
            # Add metadata
            car["created_at"] = datetime.utcnow()
            car["updated_at"] = datetime.utcnow()
            car["status"] = "available"

            # Insert
            result = cars_collection.insert_one(car)
            print(
                f"  {i}. ✓ {car['make']} {car['model']} ({car['year']}) - £{car['price']:,}"
            )

        print("\n" + "=" * 60)
        print(f"✅ Successfully seeded {len(SEED_DATA)} luxury vehicles!")
        print(f"📊 Total cars in database: {cars_collection.count_documents({})}")

        # Show breakdown by make
        print("\n📈 Inventory Breakdown:")
        pipeline = [
            {"$group": {"_id": "$make", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        breakdown = list(cars_collection.aggregate(pipeline))
        for item in breakdown:
            print(f"  • {item['_id']}: {item['count']} vehicle(s)")

        print("\n✨ Database ready for Phase 1 testing!")
        print("   Run: python app.py")

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback

        traceback.print_exc()


def load_from_json(filepath: str):
    """Load car data from JSON file (from your scraper)"""
    try:
        print(f"📂 Loading data from {filepath}...")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract cars array
        cars = data.get("cars", [])

        if not cars:
            print("⚠️  No cars found in JSON file")
            return

        print(f"✓ Found {len(cars)} cars in file")

        # Connect to MongoDB
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client["Raava_Sales"]
        cars_collection = db["Cars"]

        # Transform and insert
        inserted = 0
        for car in cars:
            # Extract relevant fields
            key_info = car.get("key_information", {})

            doc = {
                "make": key_info.get("make", "Unknown"),
                "model": key_info.get("title", "")
                .replace(key_info.get("make", ""), "")
                .strip(),
                "year": extract_year(car.get("overview", "")),
                "price": extract_price(car.get("pricing", "")),
                "mileage": extract_mileage(car.get("overview", "")),
                "fuel_type": extract_fuel_type(car.get("overview", "")),
                "body_type": extract_body_type(car.get("overview", "")),
                "style": extract_body_type(car.get("overview", "")),
                "description": car.get("overview", ""),
                "images": car.get("images", []),
                "url": car.get("url", ""),
                "source": "AutoTrader",
                "location": "UK",
                "seller_type": "Dealer",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            }

            # Only insert luxury brands
            if doc["make"] in LUXURY_MAKES and doc["price"] >= 30000:
                cars_collection.insert_one(doc)
                inserted += 1
                print(f"  ✓ {doc['make']} {doc['model']} - £{doc['price']:,}")

        print(f"\n✅ Inserted {inserted} luxury vehicles from JSON")

    except Exception as e:
        print(f"❌ Error loading JSON: {e}")


def extract_year(text: str) -> int:
    """Extract year from overview text"""
    import re

    match = re.search(r"(20\d{2})", text)
    return int(match.group(1)) if match else 2020


def extract_price(text: str) -> float:
    """Extract price from pricing text"""
    import re

    match = re.search(r"£([\d,]+)", text)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0


def extract_mileage(text: str) -> int:
    """Extract mileage from overview text"""
    import re

    match = re.search(r"([\d,]+)\s*miles", text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def extract_fuel_type(text: str) -> str:
    """Extract fuel type from overview text"""
    text_lower = text.lower()
    if "electric" in text_lower:
        return "Electric"
    elif "hybrid" in text_lower:
        return "Hybrid"
    elif "diesel" in text_lower:
        return "Diesel"
    else:
        return "Petrol"


def extract_body_type(text: str) -> str:
    """Extract body type from overview text"""
    text_lower = text.lower()
    types = ["SUV", "Coupe", "Saloon", "Hatchback", "Convertible", "Estate"]
    for body_type in types:
        if body_type.lower() in text_lower:
            return body_type
    return "Coupe"


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Load from JSON file
        json_file = sys.argv[1]
        load_from_json(json_file)
    else:
        # Use seed data
        seed_database()
