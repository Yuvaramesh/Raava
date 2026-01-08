"""
Complete System Test - Verify all components are working
"""

import sys


def test_imports():
    """Test all imports"""
    print("\n" + "=" * 70)
    print("🧪 TESTING IMPORTS")
    print("=" * 70)

    tests = []

    # Test 1: Config
    try:
        from config import (
            MONGO_CONNECTION_STRING,
            DB_NAME,
            OPENAI_API_KEY,
            SMTP_USER,
        )

        print("✅ Config imported successfully")
        tests.append(("Config", True))
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        tests.append(("Config", False))

    # Test 2: Database
    try:
        from database import db, cars_col, orders_col, conversations_col

        if db:
            print("✅ Database connected successfully")
            tests.append(("Database", True))
        else:
            print("❌ Database connection is None")
            tests.append(("Database", False))
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        tests.append(("Database", False))

    # Test 3: Managers
    try:
        from session_manager import session_manager
        from order_manager import order_manager
        from agent_prompts_manager import agent_prompts_manager

        print("✅ All managers imported successfully")
        tests.append(("Managers", True))
    except Exception as e:
        print(f"❌ Managers import failed: {e}")
        tests.append(("Managers", False))

    # Test 4: Agents
    try:
        from supervisor_agent import supervisor_agent
        from phase1_concierge import phase1_concierge

        print("✅ All agents imported successfully")
        tests.append(("Agents", True))
    except Exception as e:
        print(f"❌ Agents import failed: {e}")
        tests.append(("Agents", False))

    # Test 5: Email Service
    try:
        from enhanced_email_service import enhanced_email_service

        print("✅ Email service imported successfully")
        if enhanced_email_service.config.email_enabled:
            print("   📧 SMTP configured - emails will be sent")
        else:
            print("   ⚠️  SMTP not configured - using console mode")
        tests.append(("Email", True))
    except Exception as e:
        print(f"❌ Email service import failed: {e}")
        tests.append(("Email", False))

    # Test 6: Flask App
    try:
        from app import app

        print("✅ Flask app imported successfully")
        tests.append(("Flask App", True))
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        tests.append(("Flask App", False))

    return tests


def test_database_data():
    """Test database has data"""
    print("\n" + "=" * 70)
    print("📊 TESTING DATABASE DATA")
    print("=" * 70)

    try:
        from database import db, cars_col, orders_col

        # Count documents
        car_count = cars_col.count_documents({})
        order_count = orders_col.count_documents({})

        print(f"📦 Cars in database: {car_count}")
        print(f"📦 Orders in database: {order_count}")

        if car_count == 0:
            print("\n⚠️  No vehicles in database!")
            print("   Run: python seed_luxury_cars.py")
            return False
        else:
            print(f"\n✅ Database has {car_count} vehicles")

            # Show sample
            sample = cars_col.find_one()
            if sample:
                print(f"\n📋 Sample Vehicle:")
                print(
                    f"   {sample.get('make')} {sample.get('model')} ({sample.get('year')})"
                )
                print(f"   Price: £{sample.get('price', 0):,}")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_email_config():
    """Test email configuration"""
    print("\n" + "=" * 70)
    print("📧 TESTING EMAIL CONFIGURATION")
    print("=" * 70)

    try:
        from enhanced_email_service import enhanced_email_service

        config = enhanced_email_service.config

        print(f"SMTP Host: {config.smtp_host}")
        print(f"SMTP Port: {config.smtp_port}")
        print(f"SMTP User: {config.smtp_user}")
        print(f"From Email: {config.from_email}")
        print(f"Email Enabled: {config.email_enabled}")

        if config.email_enabled:
            print("\n🧪 Testing SMTP connection...")
            result = enhanced_email_service.test_email_configuration()
            if result:
                print("✅ Email service fully configured and working")
                return True
            else:
                print("⚠️  SMTP credentials may be incorrect")
                print("   Check your Gmail App Password")
                return False
        else:
            print("\n⚠️  Email not configured - will use console mode")
            print("   Add SMTP_USER and SMTP_PASSWORD to .env")
            return False

    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return False


def test_environment():
    """Test environment variables"""
    print("\n" + "=" * 70)
    print("🔧 TESTING ENVIRONMENT VARIABLES")
    print("=" * 70)

    try:
        from config import (
            MONGO_CONNECTION_STRING,
            DB_NAME,
            OPENAI_API_KEY,
            SMTP_USER,
            SMTP_PASSWORD,
            FROM_EMAIL,
        )

        checks = [
            ("MONGO_CONNECTION_STRING", bool(MONGO_CONNECTION_STRING)),
            ("DB_NAME", bool(DB_NAME)),
            ("OPENAI_API_KEY", bool(OPENAI_API_KEY)),
            ("SMTP_USER", bool(SMTP_USER)),
            ("SMTP_PASSWORD", bool(SMTP_PASSWORD)),
            ("FROM_EMAIL", bool(FROM_EMAIL)),
        ]

        all_passed = True
        for name, status in checks:
            symbol = "✅" if status else "❌"
            print(f"{symbol} {name}: {'Set' if status else 'NOT SET'}")
            if not status and name in ["MONGO_CONNECTION_STRING", "OPENAI_API_KEY"]:
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🚗 RAAVA PLATFORM - COMPLETE SYSTEM TEST")
    print("=" * 70)

    # Test 1: Imports
    import_tests = test_imports()

    # Test 2: Environment
    env_ok = test_environment()

    # Test 3: Database
    db_ok = test_database_data()

    # Test 4: Email
    email_ok = test_email_config()

    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)

    all_imports_ok = all(result for _, result in import_tests)

    print(
        f"\n{'✅' if all_imports_ok else '❌'} Imports: {'All passed' if all_imports_ok else 'Some failed'}"
    )
    print(
        f"{'✅' if env_ok else '⚠️ '} Environment: {'OK' if env_ok else 'Missing required variables'}"
    )
    print(
        f"{'✅' if db_ok else '❌'} Database: {'OK' if db_ok else 'No data or connection failed'}"
    )
    print(
        f"{'✅' if email_ok else '⚠️ '} Email: {'Configured' if email_ok else 'Using console mode'}"
    )

    # Recommendations
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)

    if not all_imports_ok:
        print("\n❌ CRITICAL: Fix import errors before running the app")
        print("   Check that all files are present and requirements installed")

    if not env_ok:
        print("\n❌ CRITICAL: Set required environment variables in .env file")
        print("   Required: MONGO_CONNECTION_STRING, OPENAI_API_KEY")

    if not db_ok:
        print("\n⚠️  Add sample data: python seed_luxury_cars.py")

    if not email_ok:
        print("\n⚠️  Configure email in .env to send real emails")
        print("   See SETUP_GUIDE.md for Gmail App Password instructions")

    if all_imports_ok and env_ok and db_ok:
        print("\n✅ SYSTEM READY!")
        print("\n🚀 START THE APP:")
        print("   python app.py")
        print("\n🌐 THEN VISIT:")
        print("   http://127.0.0.1:5000/chat-page")
        print("\n📝 TEST CONVERSATION:")
        print("   1. User: 'list the latest lamborghini'")
        print("   2. Bot: [Shows vehicles]")
        print("   3. User: 'option 1'")
        print("   4. Bot: [Asks payment method]")
        print("   5. User: 'cash'")
        print("   6. Bot: [Asks for details]")
        print("   7. User: 'John Smith, john@test.com, +447123456789'")
        print("   8. Bot: [Creates order and sends email]")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
