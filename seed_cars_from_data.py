"""
Seed Cars Collection from AutoTrader and Ferrari Data
Imports car data into MongoDB Cars collection
"""

from pymongo import MongoClient
from datetime import datetime
from config import MONGO_CONNECTION_STRING, DB_NAME
import re


def extract_price(pricing_text):
    """Extract price from pricing text"""
    if not pricing_text:
        return 0

    # Look for £ followed by numbers
    match = re.search(r"£([\d,]+)", pricing_text)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def extract_mileage(overview_text):
    """Extract mileage from overview"""
    if not overview_text:
        return 0

    match = re.search(r"Mileage\s*([\d,]+)\s*miles", overview_text)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def extract_year(overview_text):
    """Extract year from overview"""
    if not overview_text:
        return None

    match = re.search(r"Registration\s*(\d{4})", overview_text)
    if match:
        return int(match.group(1))

    match = re.search(r"\((\d{2})\s+reg\)", overview_text)
    if match:
        year_suffix = int(match.group(1))
        return 2000 + year_suffix if year_suffix < 50 else 1900 + year_suffix

    return None


def extract_fuel_type(overview_text):
    """Extract fuel type"""
    if not overview_text:
        return "Petrol"

    if "Electric" in overview_text:
        return "Electric"
    elif "Diesel" in overview_text:
        return "Diesel"
    elif "Hybrid" in overview_text:
        return "Hybrid"
    else:
        return "Petrol"


def extract_body_type(overview_text):
    """Extract body type"""
    if not overview_text:
        return "Hatchback"

    if "SUV" in overview_text:
        return "SUV"
    elif "Coupe" in overview_text:
        return "Coupe"
    elif "Convertible" in overview_text:
        return "Convertible"
    elif "Hatchback" in overview_text:
        return "Hatchback"
    else:
        return "Saloon"


def extract_engine(overview_text):
    """Extract engine size"""
    if not overview_text:
        return ""

    match = re.search(r"Engine\s*([\d.]+L)", overview_text)
    if match:
        return match.group(1)
    return ""


def seed_cars():
    """Seed cars collection with AutoTrader and Ferrari data"""
    print("\n" + "=" * 70)
    print("🚗 SEEDING CARS COLLECTION")
    print("=" * 70)

    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        cars_col = db["Cars"]

        # Clear existing cars
        print("\n🧹 Clearing existing cars...")
        cars_col.delete_many({})

        # Peugeot cars from AutoTrader
        peugeot_cars = [
            {
                "make": "Peugeot",
                "model": "408",
                "year": 2024,
                "price": 17050,
                "mileage": 41045,
                "fuel_type": "Petrol",
                "body_type": "Hatchback",
                "engine": "1.2L",
                "transmission": "Automatic",
                "description": "Peugeot 408 1.2 PureTech GT Fastback EAT Euro 6. Grey colour, 5 doors, good condition.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w600/062372b642ca4fbebc4c393826913434.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202510307542048",
                "source": "AutoTrader",
                "location": "New Southgate",
                "seller_type": "Dealer",
                "seller_name": "Car Planet Barnet",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Peugeot",
                "model": "208",
                "year": 2025,
                "price": 20614,
                "mileage": 5,
                "fuel_type": "Hybrid",
                "body_type": "Hatchback",
                "engine": "1.2L",
                "transmission": "Automatic",
                "description": "Nearly new Peugeot 208 1.2 HYBRID GT e-DSC6. Black colour, Peugeot approved.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w600/48f168efae6b4c2e8b70c791048e6fca.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202510026820671",
                "source": "AutoTrader",
                "location": "London",
                "seller_type": "Dealer",
                "seller_name": "Stellantis &You Chingford",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Peugeot",
                "model": "3008",
                "year": 2020,
                "price": 14301,
                "mileage": 48081,
                "fuel_type": "Petrol",
                "body_type": "SUV",
                "engine": "1.2L",
                "transmission": "Automatic",
                "description": "Peugeot 3008 1.2 PureTech GT Line Premium EAT. White colour, full dealership service history.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w600/e94495390dcc4e1f9660c3939a2cf934.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202512048360274",
                "source": "AutoTrader",
                "location": "London",
                "seller_type": "Dealer",
                "seller_name": "Stellantis &You Chingford",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Peugeot",
                "model": "E-208",
                "year": 2025,
                "price": 21698,
                "mileage": 281,
                "fuel_type": "Electric",
                "body_type": "Hatchback",
                "engine": "Electric",
                "transmission": "Automatic",
                "description": "Peugeot E-208 51kWh GT Auto. Grey colour, 263 miles range.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w600/50120db1e2ec4abd8d738406b14df5b2.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202510157158341",
                "source": "AutoTrader",
                "location": "Epsom",
                "seller_type": "Dealer",
                "seller_name": "Wilsons Peugeot",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
        ]

        # Ferrari cars
        ferrari_cars = [
            {
                "make": "Ferrari",
                "model": "488 GTB",
                "year": 2017,
                "price": 189950,
                "mileage": 8400,
                "fuel_type": "Petrol",
                "body_type": "Coupe",
                "engine": "3.9L V8 Twin-Turbo",
                "power": "660 HP",
                "transmission": "Automatic",
                "description": "Rosso Corsa over Nero leather. Full Ferrari service history. UK supplied car with only 8,400 miles. Immaculate condition.",
                "images": ["https://m.atcdn.co.uk/a/media/w800/ferrari-488-gtb-1.jpg"],
                "url": "https://www.autotrader.co.uk/car-details/ferrari-488",
                "source": "AutoTrader",
                "location": "London",
                "seller_type": "Dealer",
                "seller_name": "H.R. Owen London",
                "postcode": "SW1A 1AA",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Ferrari",
                "model": "355 F1",
                "year": 2019,
                "price": 109995,
                "mileage": 1400,
                "fuel_type": "Petrol",
                "body_type": "Coupe",
                "engine": "3.4L",
                "transmission": "Automatic",
                "description": "Ferrari 355 F1 3.4. Blue colour, 4 seats.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w600/9ec73727eca14654912c4c0b36ba2332.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202503049723102",
                "source": "AutoTrader",
                "location": "Nottingham",
                "seller_type": "Dealer",
                "seller_name": "EPJ Associates Ltd",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Ferrari",
                "model": "599",
                "year": 2006,
                "price": 79995,
                "mileage": 31000,
                "fuel_type": "Petrol",
                "body_type": "Coupe",
                "engine": "6.0L V12",
                "transmission": "Automatic",
                "description": "Ferrari 599 GTB Fiorano F1. Black colour, full service history, 2 seats.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w600/7c13cccf4e304ebfb4bda51d38fde702.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202509226517613",
                "source": "AutoTrader",
                "location": "Caen View",
                "seller_type": "Dealer",
                "seller_name": "Apex Cars Direct",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Ferrari",
                "model": "Purosangue",
                "year": 2023,
                "price": 349995,
                "mileage": 1950,
                "fuel_type": "Petrol",
                "body_type": "SUV",
                "engine": "6.5L V12",
                "transmission": "Automatic",
                "description": "Ferrari Purosangue 6.5 V12 F1 DCT 4WD. Green colour, 4 seats, full dealership service history.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w600/35c76882ef374d82aefd23274479b723.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202512268802585",
                "source": "AutoTrader",
                "location": "Newport, Isle Of Wight",
                "seller_type": "Dealer",
                "seller_name": "Riviera Sports & Prestige",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Ferrari",
                "model": "296 GTB",
                "year": 2022,
                "price": 194995,
                "mileage": 3800,
                "fuel_type": "Hybrid",
                "body_type": "Coupe",
                "engine": "3.0L V6 Plug-in Hybrid",
                "transmission": "Automatic",
                "description": "Ferrari 296 GTB 3.0T V6 7.45kWh F1 DCT. Grey colour, 16 miles electric range.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w600/706f43e7bbb34cbb8f6ef90d52366b65.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202510086974524",
                "source": "AutoTrader",
                "location": "Beverley",
                "seller_type": "Dealer",
                "seller_name": "Sasso Automotive Ltd",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Ferrari",
                "model": "Portofino",
                "year": 2019,
                "price": 122995,
                "mileage": 19800,
                "fuel_type": "Petrol",
                "body_type": "Convertible",
                "engine": "3.8L V8",
                "transmission": "Automatic",
                "description": "Ferrari Portofino 3.8T V8 F1 DCT. Red colour, 4 seats, convertible.",
                "images": [
                    "https://m.atcdn.co.uk/a/media/w800/963cd4f688454f74b3dec19c51edff89.jpg"
                ],
                "url": "https://www.autotrader.co.uk/car-details/202512108504191",
                "source": "AutoTrader",
                "location": "Nottingham",
                "seller_type": "Dealer",
                "seller_name": "SZ Motor Group Ltd",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
        ]

        # Additional luxury cars
        luxury_cars = [
            {
                "make": "Lamborghini",
                "model": "Urus",
                "year": 2023,
                "price": 175000,
                "mileage": 1200,
                "fuel_type": "Petrol",
                "body_type": "SUV",
                "engine": "4.0L V8 Twin-Turbo",
                "power": "650 HP",
                "transmission": "Automatic",
                "description": "Lamborghini Urus - The world's first Super Sport Utility Vehicle. Nero Noctis over Nero Ade leather.",
                "images": ["https://cdn.example.com/urus.jpg"],
                "url": "https://raava.com/urus",
                "source": "Raava Exclusive",
                "location": "London",
                "seller_type": "Dealer",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Lamborghini",
                "model": "Huracán EVO",
                "year": 2021,
                "price": 219950,
                "mileage": 2800,
                "fuel_type": "Petrol",
                "body_type": "Coupe",
                "engine": "5.2L V10",
                "power": "640 HP",
                "transmission": "Automatic",
                "description": "Grigio Titans over Nero Ade leather. Full Lamborghini service history.",
                "images": ["https://cdn.example.com/huracan.jpg"],
                "url": "https://raava.com/huracan",
                "source": "Raava Exclusive",
                "location": "Surrey",
                "seller_type": "Dealer",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
            {
                "make": "Porsche",
                "model": "911 Turbo S",
                "year": 2022,
                "price": 185000,
                "mileage": 3500,
                "fuel_type": "Petrol",
                "body_type": "Coupe",
                "engine": "3.8L Twin-Turbo",
                "power": "640 HP",
                "transmission": "PDK",
                "description": "Guards Red with black leather interior. Sport Chrono package, PASM.",
                "images": ["https://cdn.example.com/911-turbo-s.jpg"],
                "url": "https://raava.com/911-turbo-s",
                "source": "Raava Exclusive",
                "location": "Manchester",
                "seller_type": "Dealer",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "available",
            },
        ]

        # Combine all cars
        all_cars = peugeot_cars + ferrari_cars + luxury_cars

        # Insert all cars
        result = cars_col.insert_many(all_cars)
        print(f"\n✅ Inserted {len(result.inserted_ids)} cars into database")

        # Show summary
        print(f"\n📊 SUMMARY:")
        print(f"   • Peugeot: {len(peugeot_cars)} cars")
        print(f"   • Ferrari: {len(ferrari_cars)} cars")
        print(f"   • Other Luxury: {len(luxury_cars)} cars")
        print(f"   • Total: {len(all_cars)} cars")

        # Show some examples
        print(f"\n📋 SAMPLE CARS:")
        for i, car in enumerate(all_cars[:5], 1):
            print(
                f"   {i}. {car['make']} {car['model']} ({car['year']}) - £{car['price']:,}"
            )

        print("\n" + "=" * 70)
        print("✅ SEEDING COMPLETE")
        print("=" * 70)
        print("\n💡 NEXT STEPS:")
        print("   1. Start app: python app.py")
        print("   2. Visit: http://127.0.0.1:5000")
        print("   3. Cars will display on homepage")
        print("   4. Click 'List Your Car' to test Phase 3")
        print("\n" + "=" * 70 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    seed_cars()
