"""
Manual Test - Create appointment directly to verify everything works
RUN THIS TO TEST: python test_appointment_creation.py
"""

from datetime import datetime, timedelta


def test_appointment_creation():
    """Test creating an appointment directly"""
    print("\n" + "=" * 70)
    print("🧪 TESTING APPOINTMENT CREATION")
    print("=" * 70)

    try:
        # Import the manager
        print("\n1. Importing service_appointment_manager...")
        from service_appointment_manager import service_appointment_manager

        print("   ✅ Import successful")

        # Create test data
        print("\n2. Preparing test data...")

        vehicle = {
            "make": "Lamborghini",
            "model": "Huracan Evo",
            "year": 2021,
            "mileage": 202,
            "registration": "TEST123",
        }

        provider = {
            "name": "Apex Automotives",
            "location": "London",
            "tier": 2,
            "phone": "+44 4567 890643",
            "rating": 4.8,
            "distance_miles": 1.1,
            "estimated_cost": 8050,
        }

        tomorrow = datetime.now() + timedelta(days=2)
        appointment_date = tomorrow.strftime("%Y-%m-%d")
        appointment_time = "10:30"

        customer = {
            "name": "Want To",
            "email": "yuvi@10qbit.com",
            "phone": "+444567890643",
            "postcode": "SW1A 1AA",
            "session_id": "test-session",
        }

        print(f"\n📋 Test Data:")
        print(f"   Vehicle: {vehicle['make']} {vehicle['model']} ({vehicle['year']})")
        print(f"   Customer: {customer['name']} - {customer['email']}")
        print(f"   Provider: {provider['name']}")
        print(f"   Date: {appointment_date} at {appointment_time}")

        # Create appointment
        print("\n3. Creating appointment in database...")
        result = service_appointment_manager.create_appointment(
            vehicle=vehicle,
            service_type="upgrade",
            service_description="Upgrade for noisy brake",
            urgency="routine",
            provider=provider,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            customer=customer,
            recommendations={},
        )

        if result.get("success"):
            appointment_id = result.get("appointment_id")
            print(f"\n✅ SUCCESS!")
            print(f"   Appointment ID: {appointment_id}")

            # Verify in database
            print("\n4. Verifying in database...")
            from database import db

            if db is not None:
                services_col = db["Services"]

                # Check if appointment exists
                appointment = services_col.find_one({"appointment_id": appointment_id})

                if appointment:
                    print(f"   ✅ FOUND in Services collection")
                    print(
                        f"   Vehicle: {appointment['vehicle']['make']} {appointment['vehicle']['model']}"
                    )
                    print(f"   Customer: {appointment['customer']['name']}")
                    print(f"   Email sent: {appointment.get('email_sent', False)}")

                    # Check total count
                    total = services_col.count_documents({})
                    print(f"\n   Total appointments in Services: {total}")

                    return True
                else:
                    print(f"   ❌ NOT FOUND in database!")
                    return False
            else:
                print(f"   ⚠️ Database not connected")
                return False
        else:
            print(f"\n❌ FAILED: {result.get('message')}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_email_sending():
    """Test email sending"""
    print("\n" + "=" * 70)
    print("📧 TESTING EMAIL SENDING")
    print("=" * 70)

    try:
        print("\n1. Checking email configuration...")
        from enhanced_email_service import enhanced_email_service

        config = enhanced_email_service.config
        print(f"   Email enabled: {config.email_enabled}")

        if not config.email_enabled:
            print(f"\n⚠️  EMAIL NOT CONFIGURED")
            print(f"   Add to .env:")
            print(f"   SMTP_USER=your.email@gmail.com")
            print(f"   SMTP_PASSWORD=your_app_password")
            return False

        print(f"   SMTP: {config.smtp_host}:{config.smtp_port}")
        print(f"   From: {config.from_email}")

        print("\n2. Testing SMTP connection...")
        if enhanced_email_service.test_email_configuration():
            print(f"   ✅ SMTP connection successful")
            return True
        else:
            print(f"   ❌ SMTP connection failed")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def check_services_collection():
    """Check Services collection"""
    print("\n" + "=" * 70)
    print("📊 CHECKING SERVICES COLLECTION")
    print("=" * 70)

    try:
        from database import db

        if db is None:
            print("\n❌ Database not connected")
            return False

        services_col = db["Services"]
        total = services_col.count_documents({})

        print(f"\n📋 Total appointments: {total}")

        if total > 0:
            print(f"\n📝 Recent appointments:")
            appointments = list(services_col.find().sort("created_at", -1).limit(3))

            for i, apt in enumerate(appointments, 1):
                print(f"\n{i}. {apt.get('appointment_id')}")
                print(
                    f"   Vehicle: {apt.get('vehicle', {}).get('make')} {apt.get('vehicle', {}).get('model')}"
                )
                print(f"   Customer: {apt.get('customer', {}).get('name')}")
                print(f"   Date: {apt.get('appointment', {}).get('date')}")
                print(f"   Email sent: {apt.get('email_sent', False)}")

        return total > 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main():
    print("\n🚗 RAAVA SERVICE APPOINTMENT TEST")
    print("=" * 70)

    # Test 1: Check existing appointments
    has_existing = check_services_collection()

    # Test 2: Check email
    email_ok = test_email_sending()

    # Test 3: Create test appointment
    print("\n" + "=" * 70)
    print("🧪 CREATING TEST APPOINTMENT")
    print("=" * 70)

    response = input("\nCreate a test appointment? (y/n): ")
    if response.lower() == "y":
        success = test_appointment_creation()

        if success:
            print("\n" + "=" * 70)
            print("✅ TEST SUCCESSFUL")
            print("=" * 70)
            print("\nAppointment created and saved to Services collection!")

            if email_ok:
                print("Email should have been sent to yuvi@10qbit.com")
                print("Check your inbox!")
            else:
                print("Email configuration needed - check console logs")
        else:
            print("\n" + "=" * 70)
            print("❌ TEST FAILED")
            print("=" * 70)
            print("\nCheck the error messages above")

    print("\n" + "=" * 70)
    print("💡 NEXT STEPS")
    print("=" * 70)

    if not has_existing:
        print("\n1. Fix any errors shown above")
        print("2. Run this test again")
        print("3. Then test through the chat interface")
    else:
        print("\n✅ Services collection is working!")
        print("You can now test through the chat interface:")
        print("1. python app.py")
        print("2. Go to http://127.0.0.1:5000/chat-page")
        print("3. Complete a booking")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
