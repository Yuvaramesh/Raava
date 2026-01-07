"""
Raava Database Module
MongoDB connection and collection management
"""

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from config import (
    MONGO_CONNECTION_STRING,
    DB_NAME,
    CARS_COLLECTION,
    CONVERSATIONS_COLLECTION,
    ORDERS_COLLECTION,
    USERS_COLLECTION,
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB connections and collections"""

    def __init__(self):
        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        """Establish MongoDB connection"""
        try:
            logger.info(f"Connecting to MongoDB...")
            self.client = MongoClient(
                MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000
            )

            # Test connection
            self.client.admin.command("ping")

            self.db = self.client[DB_NAME]
            logger.info(f"✓ Connected to database: {DB_NAME}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            logger.warning(
                "⚠️  Running without database connection. Some features may not work."
            )
            # Create mock objects for development without MongoDB
            self.client = None
            self.db = None

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection from the database"""
        if self.db is not None:
            return self.db[collection_name]
        else:
            # Return a mock collection that won't crash the app
            return MockCollection(collection_name)

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")


class MockCollection:
    """Mock collection for development without MongoDB"""

    def __init__(self, name: str):
        self.name = name
        self._data = []

    def find(self, *args, **kwargs):
        """Mock find method"""
        return MockCursor(self._data)

    def find_one(self, *args, **kwargs):
        """Mock find_one method"""
        return None

    def insert_one(self, document):
        """Mock insert_one method"""
        self._data.append(document)
        return MockInsertResult()

    def insert_many(self, documents):
        """Mock insert_many method"""
        self._data.extend(documents)
        return MockInsertResult()

    def update_one(self, *args, **kwargs):
        """Mock update_one method"""
        return MockUpdateResult()

    def update_many(self, *args, **kwargs):
        """Mock update_many method"""
        return MockUpdateResult()

    def delete_one(self, *args, **kwargs):
        """Mock delete_one method"""
        return MockDeleteResult()

    def delete_many(self, *args, **kwargs):
        """Mock delete_many method"""
        self._data.clear()
        return MockDeleteResult()

    def count_documents(self, *args, **kwargs):
        """Mock count_documents method"""
        return len(self._data)

    def aggregate(self, pipeline):
        """Mock aggregate method"""
        return MockCursor([])


class MockCursor:
    """Mock cursor for iteration"""

    def __init__(self, data):
        self._data = data
        self._index = 0

    def __iter__(self):
        return iter(self._data)

    def limit(self, n):
        """Mock limit method"""
        self._data = self._data[:n]
        return self

    def sort(self, *args, **kwargs):
        """Mock sort method"""
        return self

    def skip(self, n):
        """Mock skip method"""
        self._data = self._data[n:]
        return self


class MockInsertResult:
    """Mock insert result"""

    def __init__(self):
        self.inserted_id = "mock_id_123"
        self.acknowledged = True


class MockUpdateResult:
    """Mock update result"""

    def __init__(self):
        self.matched_count = 1
        self.modified_count = 1
        self.acknowledged = True


class MockDeleteResult:
    """Mock delete result"""

    def __init__(self):
        self.deleted_count = 1
        self.acknowledged = True


# Initialize database manager
db_manager = DatabaseManager()

# Export collections
cars_col = db_manager.get_collection(CARS_COLLECTION)
conversations_col = db_manager.get_collection(CONVERSATIONS_COLLECTION)
orders_col = db_manager.get_collection(ORDERS_COLLECTION)
users_col = db_manager.get_collection(USERS_COLLECTION)

# Export database instance
db = db_manager.db
client = db_manager.client


def get_database_status():
    """Get database connection status"""
    if db_manager.client is not None:
        try:
            db_manager.client.admin.command("ping")
            return {
                "connected": True,
                "database": DB_NAME,
                "collections": {
                    "cars": cars_col.count_documents({}),
                    "conversations": conversations_col.count_documents({}),
                    "orders": orders_col.count_documents({}),
                    "users": users_col.count_documents({}),
                },
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
    else:
        return {
            "connected": False,
            "error": "Database not initialized (running in mock mode)",
        }


def initialize_database():
    """Initialize database with indexes"""
    if db_manager.db is None:
        logger.warning("Cannot initialize indexes - no database connection")
        return False

    try:
        # Create indexes for cars collection
        cars_col.create_index([("make", 1)])
        cars_col.create_index([("model", 1)])
        cars_col.create_index([("price", 1)])
        cars_col.create_index([("year", -1)])
        cars_col.create_index([("created_at", -1)])
        cars_col.create_index([("make", 1), ("model", 1)])

        # Create indexes for conversations collection
        conversations_col.create_index([("session_id", 1)])
        conversations_col.create_index([("timestamp", -1)])

        # Create indexes for orders collection
        orders_col.create_index([("order_id", 1)], unique=True)
        orders_col.create_index([("user_id", 1)])
        orders_col.create_index([("created_at", -1)])

        # Create indexes for users collection
        users_col.create_index([("email", 1)], unique=True)
        users_col.create_index([("created_at", -1)])

        logger.info("✓ Database indexes created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        return False


# Initialize indexes on import
initialize_database()


if __name__ == "__main__":
    """Test database connection"""
    print("=" * 60)
    print("🗄️  Database Connection Test")
    print("=" * 60)

    status = get_database_status()

    if status["connected"]:
        print("✓ Database connected successfully")
        print(f"Database: {status['database']}")
        print("\nCollection counts:")
        for collection, count in status["collections"].items():
            print(f"  • {collection}: {count} documents")
    else:
        print("❌ Database connection failed")
        print(f"Error: {status.get('error', 'Unknown error')}")

    print("=" * 60)
