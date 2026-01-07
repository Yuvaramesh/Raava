import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_CONNECTION_STRING = os.getenv(
    "MONGO_CONNECTION_STRING", os.getenv("MONGO_CONNECTION_STRING")
)
if not MONGO_CONNECTION_STRING:
    raise RuntimeError(
        "MONGO_CONNECTION_STRING or MONGO_CONNECTION_STRING not set in .env"
    )

# Database and collection names
DB_NAME = "Raava_Sales"
CARS_COLLECTION = "Cars"
ORDERS_COLLECTION = "Orders"
CONVERSATIONS_COLLECTION = "conversations"
USERS_COLLECTION = "users"

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "mCQMfsqGDT6IDkEKR20a")

# UK Car Dealer APIs
AUTOTRADER_API_KEY = os.getenv(
    "AUTOTRADER_API_KEY", ""
)  # Register at https://developers.autotrader.co.uk/
MOTORS_API_KEY = os.getenv(
    "MOTORS_API_KEY", ""
)  # Register at https://api.motors.co.uk/
CARGURUS_API_KEY = os.getenv("CARGURUS_API_KEY", "")

# Finance Provider APIs
ZUTO_PARTNER_ID = os.getenv("ZUTO_PARTNER_ID", "")  # Contact Zuto for partner access
SANTANDER_API_KEY = os.getenv("SANTANDER_API_KEY", "")
BLACK_HORSE_API_KEY = os.getenv("BLACK_HORSE_API_KEY", "")

# LLM Configuration
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-5-nano")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# Application Settings
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")

# Conversation Limits
QUESTION_LIMIT = 15
MAX_PROMPT_TOKENS = 3000
RECENT_TURNS_KEEP = 8

# JSON Markers
CAR_JSON_MARKER = "===CAR_JSON==="
WEB_JSON_MARKER = "===WEB_JSON==="
FINANCE_JSON_MARKER = "===FINANCE_JSON==="

# Luxury & Sports Car Filters
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

MINIMUM_LUXURY_PRICE = 30000  # £30,000 minimum for luxury category

# UK Finance Calculator Settings
ZUTO_CALCULATOR_URL = "https://www.zuto.com/car-finance-calculator/"
DEFAULT_DEPOSIT_PERCENTAGE = 10
DEFAULT_LOAN_TERM_MONTHS = 48
DEFAULT_APR = 9.9
