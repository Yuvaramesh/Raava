"""
Verify Session Clearing - Complete Test
RUN: python verify_session_clearing.py
"""

from pymongo import MongoClient
from config import MONGO_CONNECTION_STRING, DB_NAME
from datetime import datetime
import time


def clear_test_data():
    """Clear test sessions and appointments"""
    print("\n🧹 Cleaning up test data...")
    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]

        # Clear test sessions
        result = db["conversations"].delete_many({"session_id": {"$regex": "^test-"}})
        print(f"   Removed {result.deleted_count} test sessions")

        # Clear test appointments
        result = db["Services"].delete_many({"customer.email": "test@raava.com"})
        print(f"   Removed {result.deleted_count} test appointments")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def simulate_complete_flow():
    """Simulate complete appointment booking flow"""
    print("\n" + "=" * 70)
    print("🧪 SIMULATING COMPLETE APPOINTMENT FLOW")
    print("=" * 70)

    try:
        from session_manager import session_manager
        from service_appointment_manager import service_appointment_manager
=======
        from service_booking_manager import service_appointment_manager
        from datetime import timedelta
        import uuid

        # Step 1: Create session
        test_session_id = f"test-{str(uuid.uuid4())[:8]}"
        print(f"\n1️⃣ Creating session: {test_session_id}")

        session = session_manager.create_session(session_id=test_session_id)
        print(f"   ✅ Session created")
        print(f"   Stage: {session.stage}")

        # Step 2: Simulate conversation
        print(f"\n2️⃣ Simulating conversation...")
        session_manager.add_conversation_turn(
            test_session_id,
            "I need service for my Lamborghini",
            "Great! What's your vehicle?",
        )
        print(f"   ✅ Turn 1 added")

        # Step 3: Update with vehicle info
        print(f"\n3️⃣ Adding vehicle info...")
        session_manager.update_session(
            test_session_id,
            {
                "stage": "collecting_vehicle_info",
                "metadata": {
                    "vehicle_info": {
                        "make": "Lamborghini",
                        "model": "Huracan",
                        "year": 2021,
                        "mileage": 5000,
                    }
                },
            },
        )
        print(f"   ✅ Vehicle info added")

        # Step 4: Create appointment
        print(f"\n4️⃣ Creating appointment...")

        tomorrow = datetime.now() + timedelta(days=1)

        appointment_result = service_appointment_manager.create_appointment(
            vehicle={
                "make": "Lamborghini",
                "model": "Huracan",
                "year": 2021,
                "mileage": 5000,
                "registration": "TEST123",
            },
            service_type="scheduled_service",
            service_description="Annual service",
            urgency="routine",
            provider={
                "name": "Test Provider",
                "location": "London",
                "tier": 2,
                "phone": "+44123456789",
                "rating": 4.8,
                "distance_miles": 5.0,
                "estimated_cost": 500,
            },
            appointment_date=tomorrow.strftime("%Y-%m-%d"),
            appointment_time="10:00",
            customer={
                "name": "Test User",
                "email": "test@raava.com",
                "phone": "+44987654321",
                "postcode": "SW1A 1AA",
                "session_id": test_session_id,
            },
            recommendations={},
        )

        if appointment_result.get("success"):
            appointment_id = appointment_result.get("appointment_id")
            print(f"   ✅ Appointment created: {appointment_id}")

            # Step 5: Update session with appointment
            print(f"\n5️⃣ Updating session with appointment...")
            session_manager.update_session(
                test_session_id,
                {
                    "stage": "appointment_completed",
                    "metadata": {
                        "appointment_created": True,
                        "appointment_id": appointment_id,
                        "service_stage": "appointment_completed",
                    },
                },
            )
            print(f"   ✅ Session updated")

            # Step 6: End session (simulating what app.py does)
            print(f"\n6️⃣ Ending session (simulating app.py behavior)...")
            session_manager.end_session(test_session_id)
            print(f"   ✅ Session ended")

            # Step 7: Verify session is ended
            print(f"\n7️⃣ Verifying session ended...")
            from database import db

            conv_col = db["conversations"]

            ended_session = conv_col.find_one({"_id": test_session_id})
            if ended_session:
                is_ended = ended_session.get("ended", False)
                ended_at = ended_session.get("ended_at")

                print(f"   Session found in DB:")
                print(f"   - Ended: {is_ended}")
                print(f"   - Ended at: {ended_at}")

                if is_ended:
                    print(f"\n   ✅ SESSION CORRECTLY MARKED AS ENDED")
                else:
                    print(f"\n   ❌ SESSION NOT MARKED AS ENDED")
                    return False
            else:
                print(f"   ⚠️  Session not found in database")
                return False

            # Step 8: Try to get the session again (should create new one)
            print(f"\n8️⃣ Testing session retrieval after ending...")
            retrieved_session = session_manager.get_session(test_session_id)

            if retrieved_session:
                if retrieved_session.session_id == test_session_id:
                    print(f"   ✅ New session created with same ID (empty state)")
                    print(f"   Stage: {retrieved_session.stage}")
                    print(
                        f"   History: {len(retrieved_session.conversation_history)} turns"
                    )

                    if len(retrieved_session.conversation_history) == 0:
                        print(f"\n   ✅ SESSION PROPERLY CLEARED AND RESET")
                        return True
                    else:
                        print(f"\n   ❌ SESSION STILL HAS OLD DATA")
                        return False
                else:
                    print(
                        f"   ❌ Retrieved different session: {retrieved_session.session_id}"
                    )
                    return False
            else:
                print(f"   ❌ Could not retrieve session")
                return False
        else:
            print(
                f"   ❌ Appointment creation failed: {appointment_result.get('message')}"
            )
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_database_state():
    """Check current database state"""
    print("\n" + "=" * 70)
    print("📊 DATABASE STATE")
    print("=" * 70)

    try:
        client = MongoClient(MONGO_CONNECTION_STRING)
        db = client[DB_NAME]

        # Check conversations
        conv_col = db["conversations"]
        active = conv_col.count_documents({"ended": {"$ne": True}})
        ended = conv_col.count_documents({"ended": True})

        print(f"\n📋 Conversations:")
        print(f"   Active sessions: {active}")
        print(f"   Ended sessions: {ended}")

        if ended > 0:
            print(f"\n   Recent ended sessions:")
            ended_sessions = list(
                conv_col.find({"ended": True}).sort("ended_at", -1).limit(3)
            )
            for s in ended_sessions:
                session_id = s.get("_id") or s.get("session_id")
                ended_at = s.get("ended_at")
                print(f"   - {session_id}: {ended_at}")

        # Check services
        services_col = db["Services"]
        total_appointments = services_col.count_documents({})
        print(f"\n🔧 Services:")
        print(f"   Total appointments: {total_appointments}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("\n🚗 RAAVA SESSION CLEARING VERIFICATION")
    print("=" * 70)

    # Step 1: Check database state
    print("\n" + "=" * 70)
    print("STEP 1: Check Initial Database State")
    print("=" * 70)
    check_database_state()

    # Step 2: Clean test data
    print("\n" + "=" * 70)
    print("STEP 2: Clean Previous Test Data")
    print("=" * 70)
    clear_test_data()

    # Step 3: Simulate complete flow
    print("\n" + "=" * 70)
    print("STEP 3: Simulate Complete Flow")
    print("=" * 70)

    success = simulate_complete_flow()

    # Step 4: Check final state
    print("\n" + "=" * 70)
    print("STEP 4: Final Database State")
    print("=" * 70)
    check_database_state()

    # Summary
    print("\n" + "=" * 70)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 70)

    if success:
        print("\n✅ ALL TESTS PASSED")
        print("\nSession clearing is working correctly:")
        print("  1. ✅ Sessions are marked as 'ended: true'")
        print("  2. ✅ Ended sessions create fresh state on retrieval")
        print("  3. ✅ Old conversation history is cleared")
        print("  4. ✅ Appointments are saved to Services collection")

        print("\n💡 NEXT: Test in browser")
        print("  1. python app.py")
        print("  2. Go to http://127.0.0.1:5000/chat-page")
        print("  3. Complete an appointment booking")
        print("  4. After confirmation, type 'hi' again")
        print("  5. Should start fresh conversation")

        print("\n📝 What to check:")
        print("  • Console logs for '🧹 CLEARING SESSION'")
        print("  • Browser localStorage should NOT have old session_id")
        print("  • New message should start with greeting")

    else:
        print("\n❌ TESTS FAILED")
        print("\nCheck the error messages above")
        print("Most likely issues:")
        print("  1. Session manager not ending sessions properly")
        print("  2. Database not updating 'ended' flag")
        print("  3. Session retrieval not checking 'ended' status")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
