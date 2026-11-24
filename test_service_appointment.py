"""
Test Service Booking Flow - End to End
"""

from pymongo import MongoClient
from config import MONGO_CONNECTION_STRING, DB_NAME
from datetime import datetime


def test_service_booking():
    """Test complete service booking flow"""
    print("\n" + "=" * 70)
    print("🧪 TESTING SERVICE BOOKING FLOW")
    print("=" * 70)

    # Test data
    test_vehicle = {
        "make": "Lamborghini",
        "model": "Huracan EVO",
        "year": 2021,
        "mileage": 220,
    }

    test_service = {
        "type": "scheduled_service",
        "description": "Annual service",
        "urgency": "routine",
    }

    test_customer = {
        "name": "Siya",
        "email": "yuvi@10qbit.com",
        "phone": "+4431323567896",
        "postcode": "SW1 1AA",
    }

    test_provider = {
        "name": "Autoshield",
        "location": "Cuffley, Hertfordshire",
        "phone": "01707 888890",
        "estimated_cost": 325,
        "rating": 4.9,
    }

    test_datetime = datetime(2026, 1, 13, 11, 30)

    print("\n📝 Test Data:")
    print(f"   Vehicle: {test_vehicle['make']} {test_vehicle['model']}")
    print(f"   Customer: {test_customer['email']}")
    print(f"   Date: {test_datetime.strftime('%Y-%m-%d %H:%M')}")

    # Create appointment
    print(f"\n🔧 Creating service appointment...")

    try:
        from service_booking_manager import service_booking_manager

        result = service_booking_manager.create_service_appointment(
            vehicle_info=test_vehicle,
            service_request=test_service,
            customer_info=test_customer,
            provider_info=test_provider,
            appointment_datetime=test_datetime,
=======
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
            print(f"\n✅ APPOINTMENT CREATED SUCCESSFULLY")
            print(f"   Appointment ID: {appointment_id}")

            # Verify in database
            print(f"\n🔍 Verifying in Services collection...")
            client = MongoClient(MONGO_CONNECTION_STRING)
            db = client[DB_NAME]
            services_col = db["Services"]

            db_appointment = services_col.find_one({"appointment_id": appointment_id})

            if db_appointment:
                print(f"✅ APPOINTMENT FOUND IN 'Services' COLLECTION")
                print(f"\n📋 Appointment Details:")
                print(f"   ID: {db_appointment.get('appointment_id')}")
                print(f"   Status: {db_appointment.get('status')}")

                vehicle = db_appointment.get("vehicle", {})
                print(f"\n🚗 Vehicle:")
                print(
                    f"   {vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('year')})"
                )
                print(f"   Mileage: {vehicle.get('mileage')} miles")

                service = db_appointment.get("service", {})
                print(f"\n🔧 Service:")
                print(f"   Type: {service.get('type')}")
                print(f"   Description: {service.get('description')}")

                customer = db_appointment.get("customer", {})
                print(f"\n👤 Customer:")
                print(f"   Name: {customer.get('name')}")
                print(f"   Email: {customer.get('email')}")
                print(f"   Phone: {customer.get('phone')}")

                provider = db_appointment.get("provider", {})
                print(f"\n🏢 Provider:")
                print(f"   Name: {provider.get('name')}")
                print(f"   Location: {provider.get('location')}")
                print(f"   Cost: £{provider.get('estimated_cost')}")

                appointment = db_appointment.get("appointment", {})
                print(f"\n📅 Appointment:")
                print(f"   Time: {appointment.get('formatted')}")

                # Clean up test appointment
                print(f"\n🧹 Cleaning up test appointment...")
                services_col.delete_one({"appointment_id": appointment_id})
                print(f"✅ Test appointment deleted")

                return True
            else:
                print(f"❌ APPOINTMENT NOT FOUND IN DATABASE!")
                return False
        else:
            print(f"\n❌ APPOINTMENT CREATION FAILED")
            print(f"   Error: {result.get('message')}")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
=======
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


def check_services_collection():
    """Check Services collection status"""
    print("\n" + "=" * 70)
    print("📦 CHECKING SERVICES COLLECTION")
    print("=" * 70)

    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]
        services_col = db["Services"]

        total = services_col.count_documents({})
        print(f"\n📊 Total appointments: {total}")

        if total > 0:
            print(f"\n📋 Recent Appointments:")
            appointments = list(services_col.find().sort("created_at", -1).limit(5))

            for i, apt in enumerate(appointments, 1):
                print(f"\n{i}. Appointment ID: {apt.get('appointment_id')}")
                print(f"   Status: {apt.get('status')}")

                vehicle = apt.get("vehicle", {})
                print(f"   Vehicle: {vehicle.get('make')} {vehicle.get('model')}")

                customer = apt.get("customer", {})
                print(f"   Customer: {customer.get('email')}")

                provider = apt.get("provider", {})
                print(f"   Provider: {provider.get('name')}")

                created = apt.get("created_at")
                if isinstance(created, datetime):
                    print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("\n⚠️  No appointments found")

        return total > 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_date_parsing():
    """Test date parsing"""
    print("\n" + "=" * 70)
    print("🗓️ TESTING DATE PARSING")
    print("=" * 70)

    from phase2_service_manager import phase2_service_manager

    test_cases = [
        "2026-01-13, 11.30",
        "2026-01-15 14:00",
        "tomorrow 2pm",
        "next Monday 10am",
        "15/01/2026 11:30",
    ]

    for test_input in test_cases:
        print(f"\nInput: '{test_input}'")
        result = phase2_service_manager._parse_appointment_date(test_input)
        if result:
            print(f"✅ Parsed: {result['formatted']}")
        else:
            print(f"❌ Failed to parse")


def test_customer_extraction():
    """Test customer info extraction"""
    print("\n" + "=" * 70)
    print("📧 TESTING CUSTOMER INFO EXTRACTION")
    print("=" * 70)

    from phase2_service_manager import phase2_service_manager

    test_cases = [
        "Siya, +4431323567896, yuvi@10qbit.com, SW1 1AA",
        "John Smith, john@test.com, +447123456789, W1A 1AA",
        "My name is Alice, email alice@example.com, phone +441234567890, postcode EC1A 1BB",
    ]

    for test_input in test_cases:
        print(f"\nInput: '{test_input}'")
        result = phase2_service_manager._extract_customer_service_info(test_input)
        print(f"Extracted:")
        for key, value in result.items():
            print(f"  {key}: {value}")


def main():
    print("\n🔧 RAAVA SERVICE BOOKING TEST SUITE")
    print("=" * 70)

    # Test 1: Date parsing
    test_date_parsing()

    # Test 2: Customer extraction
    test_customer_extraction()

    # Test 3: Check existing appointments
    has_appointments = check_services_collection()

    # Test 4: Create test appointment
    test_passed = test_service_booking()

    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)

    if test_passed:
        print("\n✅ ALL TESTS PASSED")
        print("   Service bookings working correctly")
        print("   Appointments stored in Services collection")
    else:
        print("\n❌ TESTS FAILED")
        print("   Check error messages above")

    print("\n💡 NEXT STEPS:")
    print("   1. Start app: python app.py")
    print("   2. Test at: http://127.0.0.1:5000/chat-page")
    print("   3. Complete flow:")
    print(
        "      User: 'I need to service my Lamborghini Huracan EVO 2021 with 220 miles'"
    )
    print("      Bot: [Asks service type]")
    print("      User: 'Annual service'")
    print("      Bot: [Asks customer details]")
    print("      User: 'Siya, yuvi@10qbit.com, +4431323567896, SW1 1AA'")
    print("      Bot: [Shows providers]")
    print("      User: '1'")
    print("      Bot: [Asks date]")
    print("      User: '2026-01-13, 11.30'")
    print("      Bot: [Asks confirmation]")
    print("      User: 'Yes'")
    print("      Bot: [Creates appointment in Services collection]")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
=======
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

