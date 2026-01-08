"""
Quick Check and Seed - Verify database has vehicles
"""

from pymongo import MongoClient
from config import MONGO_CONNECTION_STRING, DB_NAME
from datetime import datetime


def check_and_seed():
    """Check if database has vehicles, seed if empty"""
    print("\n🔍 CHECKING DATABASE FOR VEHICLES")
    print("=" * 70)

    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        cars_col = db["Cars"]

        # Check car count
        total_cars = cars_col.count_documents({})
        print(f"\n📊 Total vehicles in database: {total_cars}")

        if total_cars == 0:
            print("\n⚠️  DATABASE IS EMPTY!")
            print("   Adding sample Lamborghini vehicles...")

            # Add sample Lamborghinis
            sample_cars = [
                {
                    "make": "Lamborghini",
                    "model": "Urus Base",
                    "year": 2023,
                    "price": 175000,
                    "mileage": 1200,
                    "fuel_type": "Petrol",
                    "body_type": "SUV",
                    "style": "SUV",
                    "engine": "4.0L V8 Twin-Turbo",
                    "power": "650 HP",
                    "description": "Lamborghini Urus - The world's first Super Sport Utility Vehicle",
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
                    "style": "Coupe",
                    "engine": "5.2L V10",
                    "power": "640 HP",
                    "description": "Grigio Titans over Nero Ade leather",
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
                    "make": "Lamborghini",
                    "model": "Aventador SVJ",
                    "year": 2022,
                    "price": 389950,
                    "mileage": 500,
                    "fuel_type": "Petrol",
                    "body_type": "Coupe",
                    "style": "Coupe",
                    "engine": "6.5L V12",
                    "power": "770 HP",
                    "description": "Rosso Mars with full carbon fiber package",
                    "images": ["https://cdn.example.com/aventador.jpg"],
                    "url": "https://raava.com/aventador",
                    "source": "Raava Exclusive",
                    "location": "Manchester",
                    "seller_type": "Dealer",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "status": "available",
                },
            ]

            result = cars_col.insert_many(sample_cars)
            print(f"\n✅ Added {len(result.inserted_ids)} Lamborghini vehicles")

            for i, car in enumerate(sample_cars, 1):
                print(
                    f"   {i}. {car['make']} {car['model']} ({car['year']}) - £{car['price']:,}"
                )

            print(
                "\n💡 You can add more vehicles by running: python seed_luxury_cars.py"
            )

        else:
            print("\n✅ Database has vehicles")

            # Show Lamborghini count
            lambo_count = cars_col.count_documents(
                {"make": {"$regex": "Lamborghini", "$options": "i"}}
            )
            print(f"   • Lamborghini: {lambo_count} vehicles")

            if lambo_count > 0:
                print("\n📋 Available Lamborghinis:")
                lambos = list(
                    cars_col.find(
                        {"make": {"$regex": "Lamborghini", "$options": "i"}}
                    ).limit(5)
                )
                for i, car in enumerate(lambos, 1):
                    print(
                        f"   {i}. {car.get('make')} {car.get('model')} ({car.get('year')}) - £{car.get('price', 0):,}"
                    )

        print("\n" + "=" * 70)
        print("✅ READY TO TEST")
        print("=" * 70)
        print("\n💡 NEXT STEPS:")
        print("   1. Restart app: python app.py")
        print("   2. Go to: http://127.0.0.1:5000/chat-page")
        print("   3. Test conversation:")
        print("      User: 'list the latest lamborghini'")
        print("      Bot: [Shows 3 vehicles]")
        print("      User: 'option 1'")
        print("      Bot: [Asks payment method]")
        print("      User: 'cash'")
        print("      Bot: [Asks details]")
        print("      User: 'Name, email@test.com, +1234567890'")
        print("      Bot: [Creates order]")
        print("\n" + "=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_and_seed()
