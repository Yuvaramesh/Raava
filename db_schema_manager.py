"""
Database Schema Manager - Fixed with proper exports
"""

from typing import Dict, Any, Optional
from datetime import datetime


class DatabaseSchemaManager:
    """Manages database schemas"""

    def __init__(self):
        self._db = None
        self._collection = None

    def _get_db(self):
        """Lazy load database"""
        if self._db is None:
            try:
                from database import db as database_instance

                self._db = database_instance
            except Exception as e:
                print(f"⚠️ Could not load database: {e}")
                pass
        return self._db

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        db = self._get_db()
        if db is None:
            return {"connected": False}

        try:
            collection_names = db.list_collection_names()
            collections_info = []

            for name in collection_names:
                if not name.startswith("_"):
                    try:
                        count = db[name].count_documents({})
                        collections_info.append(
                            {
                                "name": name,
                                "count": count,
                            }
                        )
                    except:
                        pass

            return {
                "connected": True,
                "database_name": db.name,
                "total_collections": len(collection_names),
                "collections": collections_info,
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def validate_document(
        self, collection_name: str, document: Dict[str, Any]
    ) -> tuple:
        """Basic validation"""
        # Simple validation - can be extended
        return True, []


# Singleton
db_schema_manager = DatabaseSchemaManager()

# Export database reference for backward compatibility
try:
    from database import (
        db,
        cars_col as cars_collection,
        orders_col as orders_collection,
        conversations_col as conversations_collection,
    )
except ImportError as e:
    print(f"⚠️ Warning: Could not import from database module: {e}")
    db = None
    cars_collection = None
    orders_collection = None
    conversations_collection = None
