"""
Raava Session Manager - Fixed lazy loading and database compatibility
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid


@dataclass
class SessionState:
    """Session state data structure"""

    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = None
    last_active: datetime = None
    stage: str = "supervisor_greeting"
    routed: bool = False
    active_agent: Optional[str] = None
    preferences: Dict[str, Any] = None
    customer_info: Dict[str, Any] = None
    payment_method: Optional[str] = None
    finance_type: Optional[str] = None
    selected_vehicle: Optional[Dict] = None
    available_vehicles: List[Dict] = None
    finance_options: Optional[Dict] = None
    order_created: bool = False
    order_id: Optional[str] = None
    conversation_history: List[Dict] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_active is None:
            self.last_active = datetime.utcnow()
        if self.preferences is None:
            self.preferences = {}
        if self.customer_info is None:
            self.customer_info = {}
        if self.available_vehicles is None:
            self.available_vehicles = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if isinstance(data.get("last_active"), datetime):
            data["last_active"] = data["last_active"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """Create from dictionary - with backward compatibility"""
        # Remove fields that aren't in SessionState
        allowed_fields = {
            "session_id",
            "user_id",
            "created_at",
            "last_active",
            "stage",
            "routed",
            "active_agent",
            "preferences",
            "customer_info",
            "payment_method",
            "finance_type",
            "selected_vehicle",
            "available_vehicles",
            "finance_options",
            "order_created",
            "order_id",
            "conversation_history",
            "metadata",
        }

        # Filter out unknown fields
        clean_data = {k: v for k, v in data.items() if k in allowed_fields}

        # Convert datetime strings
        if isinstance(clean_data.get("created_at"), str):
            clean_data["created_at"] = datetime.fromisoformat(clean_data["created_at"])
        if isinstance(clean_data.get("last_active"), str):
            clean_data["last_active"] = datetime.fromisoformat(
                clean_data["last_active"]
            )

        return cls(**clean_data)


class SessionManager:
    """Manages user sessions with memory and persistence"""

    def __init__(self, session_timeout_minutes: int = 60):
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.active_sessions: Dict[str, SessionState] = {}
        self._conversations_col = None

    def _get_db_collection(self):
        """Lazy load to avoid circular imports"""
        if self._conversations_col is None:
            try:
                from database import conversations_col

                self._conversations_col = conversations_col
            except Exception as e:
                print(f"⚠️ Could not load conversations collection: {e}")
                pass
        return self._conversations_col

    def create_session(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> SessionState:
        """Create a new session"""
        if session_id is None:
            session_id = str(uuid.uuid4())

        session_state = SessionState(session_id=session_id, user_id=user_id)
        self.active_sessions[session_id] = session_state
        self._save_session_to_db(session_state)
        print(f"✅ Created new session: {session_id}")
        return session_state

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session from memory or database"""
        # Check memory first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if self._is_session_expired(session):
                self.end_session(session_id)
                return self.create_session(session_id=session_id)
            session.last_active = datetime.utcnow()
            return session

        # Try loading from database
        session = self._load_session_from_db(session_id)
        if session:
            if self._is_session_expired(session):
                return self.create_session(session_id=session_id)
            self.active_sessions[session_id] = session
            session.last_active = datetime.utcnow()
            return session

        # Create new session
        return self.create_session(session_id=session_id)

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session state"""
        session = self.get_session(session_id)
        if not session:
            return False

        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.last_active = datetime.utcnow()
        self._save_session_to_db(session)
        return True

    def add_conversation_turn(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Dict = None,
    ) -> bool:
        """Add conversation turn"""
        session = self.get_session(session_id)
        if not session:
            return False

        turn = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": user_message,
            "ai_response": ai_response,
            "stage": session.stage,
            "active_agent": session.active_agent,
            "metadata": metadata or {},
        }

        session.conversation_history.append(turn)
        session.last_active = datetime.utcnow()
        self._save_conversation_turn_to_db(session_id, turn)
        return True

    def get_conversation_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get conversation history"""
        session = self.get_session(session_id)
        if not session:
            return []
        history = session.conversation_history
        return history[-limit:] if limit else history

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary"""
        session = self.get_session(session_id)
        if not session:
            return {}

        return {
            "session_id": session.session_id,
            "stage": session.stage,
            "active_agent": session.active_agent,
            "order_created": session.order_created,
            "order_id": session.order_id,
            "conversation_turns": len(session.conversation_history),
        }

    def end_session(self, session_id: str) -> bool:
        """End session"""
        self._mark_session_ended_in_db(session_id)
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        return True

    def cleanup_expired_sessions(self) -> int:
        """Cleanup expired sessions"""
        expired_count = 0
        expired_sessions = [
            sid
            for sid, s in self.active_sessions.items()
            if self._is_session_expired(s)
        ]
        for session_id in expired_sessions:
            self.end_session(session_id)
            expired_count += 1
        if expired_count > 0:
            print(f"🧹 Cleaned up {expired_count} expired sessions")
        return expired_count

    def _is_session_expired(self, session: SessionState) -> bool:
        """Check if expired"""
        if not session.last_active:
            return True
        return datetime.utcnow() - session.last_active > self.session_timeout

    def _save_session_to_db(self, session: SessionState) -> bool:
        """Save to database"""
        try:
            col = self._get_db_collection()
            if col is None:
                return False
            doc = session.to_dict()
            doc["_id"] = session.session_id
            doc["ended"] = False
            col.update_one({"_id": session.session_id}, {"$set": doc}, upsert=True)
            print(f"✅ Session saved to database: {session.session_id}")
            return True
        except Exception as e:
            print(f"❌ Error saving session: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _load_session_from_db(self, session_id: str) -> Optional[SessionState]:
        """Load from database"""
        try:
            col = self._get_db_collection()
            if col is None:
                return None
            doc = col.find_one({"_id": session_id, "ended": {"$ne": True}})
            if doc:
                doc.pop("_id", None)
                doc.pop("ended", None)
                print(f"✅ Session loaded from database: {session_id}")
                return SessionState.from_dict(doc)
        except Exception as e:
            print(f"❌ Error loading session: {e}")
            import traceback

            traceback.print_exc()
        return None

    def _save_conversation_turn_to_db(self, session_id: str, turn: Dict) -> bool:
        """Save conversation turn"""
        try:
            col = self._get_db_collection()
            if col is None:
                return False
            turn_doc = {
                "session_id": session_id,
                "timestamp": datetime.utcnow(),
                "user_message": turn.get("user_message"),
                "ai_response": turn.get("ai_response"),
                "stage": turn.get("stage"),
                "active_agent": turn.get("active_agent"),
                "metadata": turn.get("metadata", {}),
            }
            col.insert_one(turn_doc)
            return True
        except Exception as e:
            print(f"❌ Error saving turn: {e}")
            return False

    def _mark_session_ended_in_db(self, session_id: str) -> bool:
        """Mark as ended"""
        try:
            col = self._get_db_collection()
            if col is None:
                return False
            col.update_one(
                {"_id": session_id},
                {"$set": {"ended": True, "ended_at": datetime.utcnow()}},
            )
            return True
        except Exception as e:
            return False


# Singleton instance
session_manager = SessionManager(session_timeout_minutes=60)
