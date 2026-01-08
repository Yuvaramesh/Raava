"""
Enhanced Raava Configuration
Complete configuration with environment variables and documentation
"""

import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# MongoDB Connection
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
if not MONGO_CONNECTION_STRING:
    raise RuntimeError("MONGO_CONNECTION_STRING not set in .env file")

# Database and Collection Names (Dynamic - can be changed)
DB_NAME = os.getenv("DB_NAME", "Raava_Sales")
CARS_COLLECTION = os.getenv("CARS_COLLECTION", "Cars")
ORDERS_COLLECTION = os.getenv("ORDERS_COLLECTION", "Orders")
CONVERSATIONS_COLLECTION = os.getenv("CONVERSATIONS_COLLECTION", "conversations")
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "users")
PROMPTS_COLLECTION = os.getenv("PROMPTS_COLLECTION", "agent_prompts")
SCHEMAS_COLLECTION = os.getenv("SCHEMAS_COLLECTION", "_schemas")
EMAIL_LOGS_COLLECTION = os.getenv("EMAIL_LOGS_COLLECTION", "email_logs")
EMAIL_TEMPLATES_COLLECTION = os.getenv("EMAIL_TEMPLATES_COLLECTION", "email_templates")

# =============================================================================
# API KEYS
# =============================================================================

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in .env file")

# Tavily Search API (Optional)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ElevenLabs Voice API (Optional)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "mCQMfsqGDT6IDkEKR20a")

# =============================================================================
# UK CAR DEALER APIs (Optional)
# =============================================================================

AUTOTRADER_API_KEY = os.getenv("AUTOTRADER_API_KEY", "")
MOTORS_API_KEY = os.getenv("MOTORS_API_KEY", "")
CARGURUS_API_KEY = os.getenv("CARGURUS_API_KEY", "")

# =============================================================================
# UK FINANCE PROVIDER APIs (Optional)
# =============================================================================

ZUTO_PARTNER_ID = os.getenv("ZUTO_PARTNER_ID", "")
SANTANDER_API_KEY = os.getenv("SANTANDER_API_KEY", "")
BLACK_HORSE_API_KEY = os.getenv("BLACK_HORSE_API_KEY", "")

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# SMTP Settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# Email Sender Settings
FROM_EMAIL = os.getenv("FROM_EMAIL", "concierge@raava.com")
FROM_NAME = os.getenv("FROM_NAME", "Raava AI Concierge")
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL", FROM_EMAIL)
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@raava.com")

# Email Feature Flags
EMAIL_ENABLED = bool(SMTP_USER and SMTP_PASSWORD)
SAVE_EMAILS_TO_DB = os.getenv("SAVE_EMAILS_TO_DB", "true").lower() == "true"
EMAIL_CONSOLE_FALLBACK = os.getenv("EMAIL_CONSOLE_FALLBACK", "true").lower() == "true"

# =============================================================================
# LLM CONFIGURATION
# =============================================================================

LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

# Flask Settings
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-in-production")
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

# Company Information
COMPANY_NAME = os.getenv("COMPANY_NAME", "Raava")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "https://raava.com")

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
SESSION_CLEANUP_INTERVAL = int(os.getenv("SESSION_CLEANUP_INTERVAL", "3600"))  # seconds

# =============================================================================
# CONVERSATION LIMITS
# =============================================================================

QUESTION_LIMIT = int(os.getenv("QUESTION_LIMIT", "15"))
MAX_PROMPT_TOKENS = int(os.getenv("MAX_PROMPT_TOKENS", "3000"))
RECENT_TURNS_KEEP = int(os.getenv("RECENT_TURNS_KEEP", "8"))

# =============================================================================
# VEHICLE FILTERS
# =============================================================================

# Luxury & Sports Car Manufacturers
LUXURY_MAKES = [
    "Ferrari",
    "Lamborghini",
    "Porsche",
    "McLaren",
    "Aston Martin",
    "Bentley",
    "Rolls-Royce",
    "Maserati",
    "Jaguar",
    "Mercedes-AMG",
    "BMW M",
    "Audi RS",
    "Lexus",
    "Tesla",
]

MINIMUM_LUXURY_PRICE = int(
    os.getenv("MINIMUM_LUXURY_PRICE", "30000")
)  # £30,000 minimum

# =============================================================================
# UK FINANCE CALCULATOR SETTINGS
# =============================================================================

ZUTO_CALCULATOR_URL = "https://www.zuto.com/car-finance-calculator/"
DEFAULT_DEPOSIT_PERCENTAGE = int(os.getenv("DEFAULT_DEPOSIT_PERCENTAGE", "10"))
DEFAULT_LOAN_TERM_MONTHS = int(os.getenv("DEFAULT_LOAN_TERM_MONTHS", "48"))
DEFAULT_APR = float(os.getenv("DEFAULT_APR", "9.9"))

# =============================================================================
# JSON MARKERS (for parsing agent responses)
# =============================================================================

CAR_JSON_MARKER = "===CAR_JSON==="
WEB_JSON_MARKER = "===WEB_JSON==="
FINANCE_JSON_MARKER = "===FINANCE_JSON==="

# =============================================================================
# FEATURE FLAGS
# =============================================================================

ENABLE_SESSION_MANAGEMENT = (
    os.getenv("ENABLE_SESSION_MANAGEMENT", "true").lower() == "true"
)
ENABLE_DYNAMIC_PROMPTS = os.getenv("ENABLE_DYNAMIC_PROMPTS", "true").lower() == "true"
ENABLE_DATABASE_SCHEMAS = os.getenv("ENABLE_DATABASE_SCHEMAS", "true").lower() == "true"
ENABLE_EMAIL_SERVICE = os.getenv("ENABLE_EMAIL_SERVICE", "true").lower() == "true"
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

# Active Agents
ACTIVE_AGENTS = {
    "supervisor": True,
    "phase1_concierge": True,
    "phase2_service_manager": os.getenv("ENABLE_PHASE2", "false").lower() == "true",
    "phase3_consigner": os.getenv("ENABLE_PHASE3", "false").lower() == "true",
}

# Agent-specific settings
SUPERVISOR_TEMPERATURE = float(os.getenv("SUPERVISOR_TEMPERATURE", "0.3"))
CONCIERGE_TEMPERATURE = float(os.getenv("CONCIERGE_TEMPERATURE", "0.7"))
SERVICE_MANAGER_TEMPERATURE = float(os.getenv("SERVICE_MANAGER_TEMPERATURE", "0.6"))
CONSIGNER_TEMPERATURE = float(os.getenv("CONSIGNER_TEMPERATURE", "0.7"))

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "./logs/raava.log")

# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================


def validate_configuration():
    """Validate required configuration is present"""
    errors = []

    # Required settings
    if not MONGO_CONNECTION_STRING:
        errors.append("MONGO_CONNECTION_STRING is required")

    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required")

    # Email warnings (not required but recommended)
    if ENABLE_EMAIL_SERVICE and not (SMTP_USER and SMTP_PASSWORD):
        print("⚠️  WARNING: Email service enabled but SMTP credentials not configured")
        print("   Emails will be logged to console only")

    if errors:
        raise RuntimeError(f"Configuration errors: {', '.join(errors)}")


def get_config_summary() -> dict:
    """Get configuration summary"""
    return {
        "database": {
            "name": DB_NAME,
            "connected": bool(MONGO_CONNECTION_STRING),
        },
        "llm": {
            "model": LLM_MODEL_NAME,
            "temperature": LLM_TEMPERATURE,
        },
        "email": {
            "enabled": EMAIL_ENABLED,
            "from": FROM_EMAIL,
            "smtp_host": SMTP_HOST,
        },
        "session": {
            "timeout_minutes": SESSION_TIMEOUT_MINUTES,
            "max_history": MAX_CONVERSATION_HISTORY,
        },
        "features": {
            "session_management": ENABLE_SESSION_MANAGEMENT,
            "dynamic_prompts": ENABLE_DYNAMIC_PROMPTS,
            "database_schemas": ENABLE_DATABASE_SCHEMAS,
            "email_service": ENABLE_EMAIL_SERVICE,
            "web_search": ENABLE_WEB_SEARCH,
        },
        "agents": ACTIVE_AGENTS,
    }


# Validate on import
try:
    validate_configuration()
    print("✅ Configuration validated successfully")
except Exception as e:
    print(f"❌ Configuration validation failed: {e}")
    raise


if __name__ == "__main__":
    """Display configuration summary"""
    print("\n" + "=" * 70)
    print("⚙️  RAAVA CONFIGURATION SUMMARY")
    print("=" * 70)

    summary = get_config_summary()

    print("\n📊 Database:")
    print(f"   Name: {summary['database']['name']}")
    print(f"   Connected: {summary['database']['connected']}")

    print("\n🤖 LLM:")
    print(f"   Model: {summary['llm']['model']}")
    print(f"   Temperature: {summary['llm']['temperature']}")

    print("\n📧 Email:")
    print(f"   Enabled: {summary['email']['enabled']}")
    print(f"   From: {summary['email']['from']}")
    print(f"   SMTP: {summary['email']['smtp_host']}")

    print("\n💾 Session:")
    print(f"   Timeout: {summary['session']['timeout_minutes']} minutes")
    print(f"   Max History: {summary['session']['max_history']} messages")

    print("\n🎯 Features:")
    for feature, enabled in summary["features"].items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {feature.replace('_', ' ').title()}")

    print("\n🤖 Agents:")
    for agent, active in summary["agents"].items():
        status = "✅" if active else "⏸️"
        print(f"   {status} {agent.replace('_', ' ').title()}")

    print("\n" + "=" * 70 + "\n")
