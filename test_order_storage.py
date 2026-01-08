"""
Test Order Creation - Verify orders are saving to Orders collection
"""

from pymongo import MongoClient
from config import MONGO_CONNECTION_STRING, DB_NAME
from order_manager import order_manager
from datetime import datetime


def test_order_creation():
    """Test creating an order directly"""
    print("\n" + "=" * 70)
    print("🧪 TESTING ORDER CREATION")
    print("=" * 70)

    # Test vehicle
    test_vehicle = {
        "make": "Ferrari",
        "model": "SF90 Stradale",
        "year": 2024,
        "price": 299950,
        "mileage": 1600,
        "fuel_type": "Hybrid",
        "body_type": "Coupe",
        "location": "Manchester",
        "source": "Test",
    }

    # Test customer
    test_customer = {
        "name": "Test Customer",
        "email": "test@raava.com",
        "phone": "+447123456789",
        "address": "123 Test St, London",
        "postcode": "W1A 1AA",
    }

    # Test finance
    test_finance = {
        "type": "PCP",
        "provider": "Santander Consumer",
        "monthly_payment": 2500.00,
        "deposit_amount": 29995.00,
        "term_months": 48,
        "apr": 8.9,
        "total_cost": 149995.00,
        "balloon_payment": 89985.00,
    }

    print("\n📝 Creating test order...")
    print(f"   Vehicle: {test_vehicle['make']} {test_vehicle['model']}")
    print(f"   Customer: {test_customer['email']}")
    print(f"   Payment: PCP Finance")

    # Create order
    result = order_manager.create_order(
        order_type="purchase",
        vehicle=test_vehicle,
        customer=test_customer,
        finance_details=test_finance,
    )

    if result.get("success"):
        order_id = result.get("order_id")
        print(f"\n✅ ORDER CREATED SUCCESSFULLY")
        print(f"   Order ID: {order_id}")

        # Verify in database
        print(f"\n🔍 Verifying in database...")
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        orders_col = db["Orders"]

        db_order = orders_col.find_one({"order_id": order_id})

        if db_order:
            print(f"✅ ORDER FOUND IN 'Orders' COLLECTION")
            print(f"\n📋 Order Details:")
            print(f"   Order ID: {db_order.get('order_id')}")
            print(f"   Status: {db_order.get('status')}")
            print(f"   Type: {db_order.get('order_type')}")

            vehicle = db_order.get("vehicle", {})
            print(f"\n🚗 Vehicle:")
            print(f"   Make: {vehicle.get('make')}")
            print(f"   Model: {vehicle.get('model')}")
            print(f"   Price: £{vehicle.get('price', 0):,}")

            customer = db_order.get("customer", {})
            print(f"\n👤 Customer:")
            print(f"   Name: {customer.get('name')}")
            print(f"   Email: {customer.get('email')}")

            finance = db_order.get("finance", {})
            if finance:
                print(f"\n💰 Finance:")
                print(f"   Type: {finance.get('type')}")
                print(f"   Monthly: £{finance.get('monthly_payment', 0):,.2f}")
                print(f"   Provider: {finance.get('provider')}")

            # Clean up test order
            print(f"\n🧹 Cleaning up test order...")
            orders_col.delete_one({"order_id": order_id})
            print(f"✅ Test order deleted")

            return True
        else:
            print(f"❌ ORDER NOT FOUND IN DATABASE!")
            return False
    else:
        print(f"\n❌ ORDER CREATION FAILED")
        print(f"   Error: {result.get('message')}")
        return False


def check_existing_orders():
    """Check existing orders in database"""
    print("\n" + "=" * 70)
    print("📦 CHECKING EXISTING ORDERS")
    print("=" * 70)

    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        orders_col = db["Orders"]

        total = orders_col.count_documents({})
        print(f"\n📊 Total orders in database: {total}")

        if total > 0:
            print(f"\n📋 Recent Orders:")
            orders = list(orders_col.find().sort("created_at", -1).limit(5))

            for i, order in enumerate(orders, 1):
                print(f"\n{i}. Order ID: {order.get('order_id')}")
                print(f"   Status: {order.get('status')}")

                vehicle = order.get("vehicle", {})
                print(f"   Vehicle: {vehicle.get('make')} {vehicle.get('model')}")
                print(f"   Price: £{vehicle.get('price', 0):,}")

                customer = order.get("customer", {})
                print(f"   Customer: {customer.get('email')}")

                created = order.get("created_at")
                if isinstance(created, datetime):
                    print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("\n⚠️  No orders found")
            print("   Create orders through the chat interface:")
            print("   1. Go to http://127.0.0.1:5000/chat-page")
            print("   2. Select a vehicle")
            print("   3. Choose payment method (Cash/Finance)")
            print("   4. Provide customer details")
            print("   5. Confirm order")

        return total > 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("\n🚗 RAAVA ORDER STORAGE TEST")
    print("=" * 70)

    # Test 1: Check existing orders
    has_orders = check_existing_orders()

    # Test 2: Create test order
    test_passed = test_order_creation()

    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)

    if test_passed:
        print("\n✅ ALL TESTS PASSED")
        print("   Orders are being saved correctly to 'Orders' collection")
    else:
        print("\n❌ TESTS FAILED")
        print("   Check error messages above")

    print("\n💡 NEXT STEPS:")
    print("   1. Start app: python app.py")
    print("   2. Test full flow at: http://127.0.0.1:5000/chat-page")
    print("   3. Complete conversation:")
    print("      - Select vehicle")
    print("      - Choose Cash or Finance")
    print("      - Provide name, email, phone")
    print("      - Confirm order")
    print("   4. Check orders: python test_order_creation.py")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
