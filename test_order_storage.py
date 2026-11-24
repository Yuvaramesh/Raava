
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
=======
from datetime import datetime
import sys


def test_database_connection():
    """Test 1: Verify database connection"""
    print("\n" + "=" * 70)
    print("TEST 1: DATABASE CONNECTION")
    print("=" * 70)

    try:
        client = MongoClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]

        # Ping database
        db.command("ping")
        print("✅ Database connection successful")

        # Check Orders collection
        orders_col = db["Orders"]
        count = orders_col.count_documents({})
        print(f"✅ Orders collection accessible ({count} documents)")

        return True, db, orders_col

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False, None, None


def test_order_creation():
    """Test 2: Create a test order"""
    print("\n" + "=" * 70)
    print("TEST 2: ORDER CREATION")
    print("=" * 70)

    try:
        from order_manager import order_manager

        # Test data
        test_vehicle = {
            "make": "Vauxhall",
            "model": "Grandland Ultimate SUV",
            "year": 2024,
            "price": 35000,
            "mileage": 0,
            "fuel_type": "Petrol",
            "body_type": "SUV",
            "title": "Vauxhall Grandland Ultimate SUV (2024)",
            "source": "Test System",
        }

        test_customer = {
            "name": "Swas",
            "email": "yuvi@10qbit.com",
            "phone": "+48983348393",
            "address": "Test Address",
            "postcode": "SW1A 1AA",
        }

        print("\n📝 Creating order...")
        print(f"   Vehicle: {test_vehicle['make']} {test_vehicle['model']}")
        print(f"   Customer: {test_customer['name']} ({test_customer['email']})")
        print(f"   Payment: Cash")

        # Create order
        result = order_manager.create_order(
            order_type="purchase",
            vehicle=test_vehicle,
            customer=test_customer,
            finance_details=None,  # Cash payment
        )

        if result.get("success"):
            order_id = result.get("order_id")
            print(f"\n✅ ORDER CREATED")
            print(f"   Order ID: {order_id}")
            print(f"   Email sent: {result.get('email_sent')}")

            return True, order_id
        else:
            print(f"\n❌ ORDER CREATION FAILED")
            print(f"   Error: {result.get('message')}")
            return False, None

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback

        traceback.print_exc()
        return False, None


def test_database_verification(db, order_id):
    """Test 3: Verify order in database"""
    print("\n" + "=" * 70)
    print("TEST 3: DATABASE VERIFICATION")
    print("=" * 70)

    try:
        orders_col = db["Orders"]

        print(f"\n🔍 Searching for order {order_id}...")
        order = orders_col.find_one({"order_id": order_id})

        if order:
            print(f"✅ ORDER FOUND IN DATABASE")
            print(f"\n📋 Order Details:")
            print(f"   Order ID: {order.get('order_id')}")
            print(f"   Status: {order.get('status')}")
            print(f"   Type: {order.get('order_type')}")

            vehicle = order.get("vehicle", {})
            print(f"\n🚗 Vehicle:")
            print(f"   Title: {vehicle.get('title')}")
            print(f"   Make: {vehicle.get('make')}")
            print(f"   Model: {vehicle.get('model')}")
            print(f"   Year: {vehicle.get('year')}")
            print(f"   Price: £{vehicle.get('price', 0):,}")

            customer = order.get("customer", {})
            print(f"\n👤 Customer:")
            print(f"   Name: {customer.get('name')}")
            print(f"   Email: {customer.get('email')}")
            print(f"   Phone: {customer.get('phone')}")

            print(f"\n💰 Financial:")
            print(f"   Total Amount: £{order.get('total_amount', 0):,}")

            created = order.get("created_at")
            if isinstance(created, datetime):
                print(f"\n📅 Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")

            return True, order
        else:
            print(f"❌ ORDER NOT FOUND IN DATABASE")
            print(f"   This is a critical error!")
            return False, None

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False, None


def test_email_configuration():
    """Test 4: Check email configuration"""
    print("\n" + "=" * 70)
    print("TEST 4: EMAIL CONFIGURATION")
    print("=" * 70)

    try:
        from enhanced_email_service import enhanced_email_service

        config = enhanced_email_service.config

        print(f"\n📧 Email Configuration:")
        print(f"   SMTP Host: {config.smtp_host}")
        print(f"   SMTP Port: {config.smtp_port}")
        print(f"   SMTP User: {config.smtp_user}")
        print(f"   From Email: {config.from_email}")
        print(f"   From Name: {config.from_name}")
        print(f"   Email Enabled: {config.email_enabled}")

        if config.email_enabled:
            print(f"\n✅ Email service is configured")
            print(f"   Emails will be sent via SMTP")
        else:
            print(f"\n⚠️  Email service not fully configured")
            print(f"   Emails will be logged to console only")
            print(f"\n💡 To enable emails, add to .env:")
            print(f"   SMTP_USER=your-email@gmail.com")
            print(f"   SMTP_PASSWORD=your-app-password")

        return config.email_enabled

    except Exception as e:
        print(f"❌ Email configuration check failed: {e}")
        return False


def cleanup_test_order(db, order_id):
    """Clean up test order"""
    print("\n" + "=" * 70)
    print("CLEANUP")
    print("=" * 70)

    try:
        orders_col = db["Orders"]

        print(f"\n🧹 Deleting test order {order_id}...")
        result = orders_col.delete_one({"order_id": order_id})

        if result.deleted_count > 0:
            print(f"✅ Test order deleted")
        else:
            print(f"⚠️  Test order not found (may have been deleted already)")

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def show_summary(tests_passed):
    """Show test summary"""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    total_tests = len(tests_passed)
    passed = sum(tests_passed.values())

    print(f"\nTests Passed: {passed}/{total_tests}")

    for test_name, result in tests_passed.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")

    if passed == total_tests:
        print("\n🎉 ALL TESTS PASSED")
        print("\nYour order system is working correctly:")
        print("  ✅ Database connection working")
        print("  ✅ Orders being created")
        print("  ✅ Orders being saved to database")
        print("  ✅ Email configuration checked")

        print("\n📝 Next Steps:")
        print("  1. Start the app: python app.py")
        print("  2. Go to: http://127.0.0.1:5000/chat-page")
        print("  3. Test the full conversation flow")

        print("\n💬 Test Conversation:")
        print('  User: "I want to buy a Lamborghini"')
        print("  Bot: [Shows vehicles]")
        print('  User: "1"')
        print('  Bot: "Cash payment or financing?"')
        print('  User: "cash"')
        print('  Bot: "Your full name?"')
        print('  User: "Swas"')
        print('  Bot: "Your email address?"')
        print('  User: "yuvi@10qbit.com"')
        print('  Bot: "Your mobile number?"')
        print('  User: "+48983348393"')
        print("  Bot: [Creates order, sends email, shows confirmation]")

    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease fix the failing tests before proceeding")

        if not tests_passed.get("Database Connection"):
            print("\n🔧 Fix Database Connection:")
            print("  1. Check MONGO_CONNECTION_STRING in .env")
            print("  2. Verify MongoDB is accessible")
            print("  3. Check network/firewall settings")

        if not tests_passed.get("Order Creation"):
            print("\n🔧 Fix Order Creation:")
            print("  1. Check order_manager.py imports")
            print("  2. Verify database collections exist")
            print("  3. Review error messages above")

        if not tests_passed.get("Database Verification"):
            print("\n🔧 Fix Database Verification:")
            print("  1. Order may not be saving correctly")
            print("  2. Check MongoDB write permissions")
            print("  3. Review order_manager.py insert logic")


def main():
    """Run all tests"""
    print("\n🚗 RAAVA ORDER SYSTEM - COMPLETE TEST SUITE")
    print("=" * 70)

    tests_passed = {}

    # Test 1: Database Connection
    db_ok, db, orders_col = test_database_connection()
    tests_passed["Database Connection"] = db_ok

    if not db_ok:
        print("\n❌ Cannot proceed - database connection failed")
        show_summary(tests_passed)
        return

    # Test 2: Order Creation
    order_ok, order_id = test_order_creation()
    tests_passed["Order Creation"] = order_ok

    if not order_ok:
        print("\n❌ Cannot proceed - order creation failed")
        show_summary(tests_passed)
        return

    # Test 3: Database Verification
    verify_ok, order = test_database_verification(db, order_id)
    tests_passed["Database Verification"] = verify_ok

    # Test 4: Email Configuration
    email_ok = test_email_configuration()
    tests_passed["Email Configuration"] = email_ok

    # Cleanup
    if order_id:
        cleanup_test_order(db, order_id)

    # Summary
    show_summary(tests_passed)

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
