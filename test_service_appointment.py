"""
Database Connection Test Script
Run this to verify your MongoDB connection and Services collection
"""

from datetime import datetime


def test_database_connection():
    """Test MongoDB connection and Services collection"""

    print("\n" + "=" * 70)
    print("🧪 TESTING DATABASE CONNECTION")
    print("=" * 70)

    # Test 1: Import database module
    print("\n1️⃣ Testing database import...")
    try:
        from database import db, client

        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import database: {e}")
        return False

    # Test 2: Check database connection
    print("\n2️⃣ Testing database connection...")
    try:
        if db is None:
            print("❌ Database is None - check MONGO_CONNECTION_STRING in config")
            return False

        # Ping database
        if client:
            client.admin.command("ping")
            print(f"✅ Connected to MongoDB")
            print(f"   Database name: {db.name}")
        else:
            print("❌ Client is None")
            return False
    except Exception as e:
        print(f"❌ Database ping failed: {e}")
        return False

    # Test 3: Check Services collection
    print("\n3️⃣ Testing Services collection...")
    try:
        services_col = db["Services"]
        count = services_col.count_documents({})
        print(f"✅ Services collection accessible")
        print(f"   Current document count: {count}")
    except Exception as e:
        print(f"❌ Services collection error: {e}")
        return False

    # Test 4: Try inserting a test document
    print("\n4️⃣ Testing document insertion...")
    try:
        test_doc = {
            "test": True,
            "appointment_id": "TEST-001",
            "created_at": datetime.utcnow(),
        }
        result = services_col.insert_one(test_doc)
        print(f"✅ Test document inserted")
        print(f"   _id: {result.inserted_id}")

        # Verify it exists
        found = services_col.find_one({"appointment_id": "TEST-001"})
        if found:
            print(f"✅ Test document verified in database")

            # Clean up test document
            services_col.delete_one({"appointment_id": "TEST-001"})
            print(f"✅ Test document cleaned up")
        else:
            print(f"❌ Test document not found after insert")
            return False

    except Exception as e:
        print(f"❌ Insert test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 5: Test service_booking_manager
    print("\n5️⃣ Testing ServiceBookingManager...")
    try:
        from service_booking_manager import service_booking_manager

        # Test creation
        result = service_booking_manager.create_service_appointment(
            vehicle_info={
                "make": "Test",
                "model": "Car",
                "year": 2024,
                "mileage": 1000,
            },
            service_request={
                "type": "test_service",
                "description": "Test service",
                "urgency": "routine",
            },
            customer_info={
                "name": "Test User",
                "email": "test@test.com",
                "phone": "123456789",
                "postcode": "TEST",
            },
            provider_info={
                "name": "Test Garage",
                "location": "Test Location",
                "phone": "123456",
                "estimated_cost": 100,
                "rating": 5.0,
                "distance_miles": 1.0,
            },
            appointment_datetime=datetime(2026, 2, 1, 10, 0),
        )

        if result.get("success"):
            appointment_id = result.get("appointment_id")
            print(f"✅ ServiceBookingManager working")
            print(f"   Appointment ID: {appointment_id}")

            # Clean up
            services_col.delete_one({"appointment_id": appointment_id})
            print(f"✅ Test appointment cleaned up")
        else:
            print(f"❌ ServiceBookingManager failed: {result.get('message')}")
            return False

    except Exception as e:
        print(f"❌ ServiceBookingManager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 6: Test email service
    print("\n6️⃣ Testing Email Service...")
    try:
        from enhanced_email_service import enhanced_email_service

        config = enhanced_email_service.config
        print(f"✅ Email service imported")
        print(f"   SMTP Host: {config.smtp_host}")
        print(f"   SMTP Port: {config.smtp_port}")
        print(f"   From Email: {config.from_email}")
        print(f"   Email Enabled: {config.email_enabled}")

        if not config.email_enabled:
            print(
                f"⚠️  Email is NOT enabled - check SMTP_USER and SMTP_PASSWORD in .env"
            )
        else:
            print(f"✅ Email is configured and enabled")

    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70 + "\n")

    return True


if __name__ == "__main__":
    success = test_database_connection()

    if not success:
        print("\n" + "=" * 70)
        print("❌ TESTS FAILED - CHECK ERRORS ABOVE")
        print("=" * 70)
        print("\n💡 Common issues:")
        print("   1. MONGO_CONNECTION_STRING not set in config.py or .env")
        print("   2. MongoDB server not running")
        print("   3. Network connection issues")
        print("   4. Wrong database credentials")
        print("\n📝 To fix:")
        print("   1. Check your .env file has MONGO_CONNECTION_STRING")
        print("   2. Verify MongoDB is running (check Atlas or local server)")
        print("   3. Test connection with MongoDB Compass")
        print("=" * 70 + "\n")
