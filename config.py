"""
Raava Luxury Automotive Platform - Configuration
Central configuration for Phase 1: Marketplace Aggregation + Finance Assessment
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# Database and collection names
DB_NAME = "Raava_Sales"
CARS_COLLECTION = "Cars"
CONVERSATIONS_COLLECTION = "conversations"
ORDERS_COLLECTION = "orders"
USERS_COLLECTION = "users"

# ============================================================================
# AI/LLM CONFIGURATION
# ============================================================================

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-5-nano")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# Embeddings Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# ============================================================================
# VOICE/TTS CONFIGURATION
# ============================================================================

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv(
    "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel voice
)
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2")

# Voice Settings
VOICE_STABILITY = float(os.getenv("VOICE_STABILITY", "0.5"))
VOICE_SIMILARITY_BOOST = float(os.getenv("VOICE_SIMILARITY_BOOST", "0.75"))

# ============================================================================
# UK CAR DEALER API KEYS
# ============================================================================

# AutoTrader API
AUTOTRADER_API_KEY = os.getenv("AUTOTRADER_API_KEY", "")
AUTOTRADER_BASE_URL = "https://api.autotrader.co.uk/v1"

# Motors.co.uk API
MOTORS_API_KEY = os.getenv("MOTORS_API_KEY", "")
MOTORS_BASE_URL = "https://api.motors.co.uk/v1"

# CarGurus API
CARGURUS_API_KEY = os.getenv("CARGURUS_API_KEY", "")
CARGURUS_BASE_URL = "https://api.cargurus.co.uk/v1"

# PistonHeads API (if available)
PISTONHEADS_API_KEY = os.getenv("PISTONHEADS_API_KEY", "")
PISTONHEADS_BASE_URL = "https://www.pistonheads.com/classifieds"

# ============================================================================
# UK FINANCE PROVIDER API KEYS
# ============================================================================

# Zuto API
ZUTO_PARTNER_ID = os.getenv("ZUTO_PARTNER_ID", "")
ZUTO_API_KEY = os.getenv("ZUTO_API_KEY", "")
ZUTO_BASE_URL = "https://api.zuto.com/v1"

# Santander Consumer Finance API
SANTANDER_API_KEY = os.getenv("SANTANDER_API_KEY", "")
SANTANDER_BASE_URL = "https://api.santanderconsumer.co.uk/v1"

# Black Horse Finance API
BLACK_HORSE_API_KEY = os.getenv("BLACK_HORSE_API_KEY", "")
BLACK_HORSE_BASE_URL = "https://api.blackhorse.co.uk/v1"

# Close Brothers Motor Finance API
CLOSE_BROTHERS_API_KEY = os.getenv("CLOSE_BROTHERS_API_KEY", "")
CLOSE_BROTHERS_BASE_URL = "https://api.closebrothers.com/v1"

# MotoNovo Finance API
MOTONOVO_API_KEY = os.getenv("MOTONOVO_API_KEY", "")
MOTONOVO_BASE_URL = "https://api.motonovo.co.uk/v1"

# ============================================================================
# LUXURY VEHICLE CONFIGURATION
# ============================================================================

# Luxury brands focused on by Raava
LUXURY_MAKES = [
    "Ferrari",
    "Lamborghini",
    "Porsche",
    "McLaren",
    "Aston Martin",
    "Bentley",
    "Rolls-Royce",
    "Mercedes-AMG",
    "BMW M",
    "Audi RS",
    "Maserati",
    "Bugatti",
    "Koenigsegg",
    "Pagani",
]

# Performance/Sports brands also supported
PERFORMANCE_MAKES = [
    "Lotus",
    "Alpine",
    "TVR",
    "Morgan",
    "Caterham",
    "Ariel",
    "BAC",
]

# Minimum price threshold for luxury vehicles (GBP)
MINIMUM_LUXURY_PRICE = 30000

# Maximum price for initial Phase 1 (can be increased)
MAXIMUM_LUXURY_PRICE = 500000

# ============================================================================
# FINANCE CALCULATION DEFAULTS
# ============================================================================

# Default finance parameters
DEFAULT_DEPOSIT_PERCENTAGE = 10.0  # 10% deposit
DEFAULT_LOAN_TERM_MONTHS = 48  # 4 years
DEFAULT_APR = 9.9  # Representative APR

# Available loan terms (months)
AVAILABLE_LOAN_TERMS = [12, 24, 36, 48, 60, 72]

# Minimum deposit percentages
MIN_DEPOSIT_PERCENTAGE = 5.0
MAX_DEPOSIT_PERCENTAGE = 50.0

# Credit score categories and typical APR adjustments
CREDIT_SCORE_CATEGORIES = {
    "Excellent": {"description": "750+", "apr_adjustment": -1.0},
    "Good": {"description": "700-749", "apr_adjustment": 0.0},
    "Fair": {"description": "650-699", "apr_adjustment": 2.0},
    "Poor": {"description": "<650", "apr_adjustment": 5.0},
}

# PCP (Personal Contract Purchase) defaults
PCP_GMFV_PERCENTAGE = 35.0  # Guaranteed Minimum Future Value
PCP_MILEAGE_ALLOWANCE = 10000  # Miles per year
PCP_EXCESS_MILEAGE_CHARGE = 0.15  # Per mile (GBP)

# ============================================================================
# SEARCH & FILTERING DEFAULTS
# ============================================================================

# Default search radius (miles)
DEFAULT_SEARCH_RADIUS = 50

# Default postcode (Central London)
DEFAULT_POSTCODE = "SW1A 1AA"

# Maximum search results per source
MAX_RESULTS_PER_SOURCE = 20

# Total maximum results to return
MAX_TOTAL_RESULTS = 50

# ============================================================================
# SCRAPING CONFIGURATION
# ============================================================================

# User agent for web scraping
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Request timeout (seconds)
REQUEST_TIMEOUT = 15

# Rate limiting (seconds between requests)
RATE_LIMIT_DELAY = 2.0

# Maximum retries for failed requests
MAX_RETRIES = 3

# ============================================================================
# FLASK APPLICATION CONFIGURATION
# ============================================================================

# Flask secret key
FLASK_SECRET_KEY = os.getenv(
    "FLASK_SECRET_KEY", "raava-luxury-automotive-2024-change-in-production"
)

# Flask debug mode
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# Flask host and port
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# Session configuration
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
PERMANENT_SESSION_LIFETIME = SESSION_TIMEOUT_MINUTES * 60

# ============================================================================
# PAYMENT & ESCROW CONFIGURATION (Phase 2)
# ============================================================================

# Stripe Configuration (for Phase 2)
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Escrow settings
ESCROW_ENABLED = os.getenv("ESCROW_ENABLED", "False").lower() == "true"
ESCROW_FEE_PERCENTAGE = float(os.getenv("ESCROW_FEE_PERCENTAGE", "2.5"))

# ============================================================================
# EMAIL CONFIGURATION (Phase 2)
# ============================================================================

# SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

# Email settings
EMAIL_FROM = os.getenv("EMAIL_FROM", "concierge@raava.co.uk")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Raava Concierge")

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Log file path
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/raava.log")

# Enable detailed logging
DETAILED_LOGGING = os.getenv("DETAILED_LOGGING", "False").lower() == "true"

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Phase 1 features
FEATURE_MARKETPLACE_AGGREGATION = True
FEATURE_FINANCE_CALCULATOR = True
FEATURE_AI_CONCIERGE = True
FEATURE_VOICE_SYNTHESIS = os.getenv("FEATURE_VOICE_SYNTHESIS", "True").lower() == "true"

# Phase 2 features (to be enabled later)
FEATURE_ESCROW_PAYMENT = False
FEATURE_DELIVERY_TRACKING = False
FEATURE_DOCUMENT_MANAGEMENT = False

# Phase 3 features (future)
FEATURE_INSURANCE_INTEGRATION = False
FEATURE_MAINTENANCE_TRACKING = False
FEATURE_VALUATION_TRACKING = False

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

# Redis configuration (for production caching)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "False").lower() == "true"

# Cache TTL (seconds)
CACHE_TTL_VEHICLE_SEARCH = int(os.getenv("CACHE_TTL_VEHICLE_SEARCH", "3600"))  # 1 hour
CACHE_TTL_FINANCE_QUOTE = int(
    os.getenv("CACHE_TTL_FINANCE_QUOTE", "1800")
)  # 30 minutes

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Rate limiting (requests per minute)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

# API key for internal services
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

# ============================================================================
# VALIDATION & CONSTRAINTS
# ============================================================================


# Validate critical configuration
def validate_config():
    """Validate that critical configuration values are set"""
    errors = []

    if not MONGO_URI:
        errors.append("MONGO_URI is not set")

    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not set - AI Concierge will not work")

    if FEATURE_VOICE_SYNTHESIS and not ELEVENLABS_API_KEY:
        errors.append("ELEVENLABS_API_KEY is not set - Voice synthesis disabled")

    if errors:
        print("\n⚠️  Configuration Warnings:")
        for error in errors:
            print(f"  • {error}")
        print()

    return len(errors) == 0


# Run validation on import
validate_config()

# ============================================================================
# EXPORT CONFIGURATION SUMMARY
# ============================================================================


def print_config_summary():
    """Print configuration summary for debugging"""
    print("=" * 60)
    print("🚗 Raava Configuration Summary")
    print("=" * 60)
    print(f"Database: {MONGO_URI[:30]}...")
    print(f"LLM Model: {LLM_MODEL_NAME}")
    print(f"Voice Enabled: {bool(ELEVENLABS_API_KEY)}")
    print(f"Luxury Brands: {len(LUXURY_MAKES)} brands")
    print(f"Min Price: £{MINIMUM_LUXURY_PRICE:,}")
    print(f"Finance Providers: Zuto, Santander, Black Horse, Close Brothers, MotoNovo")
    print(f"Car Dealers: AutoTrader, Motors, CarGurus, PistonHeads")
    print("=" * 60)


# Print summary if run directly
if __name__ == "__main__":
    print_config_summary()
