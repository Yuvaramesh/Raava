"""
Agent Prompts Manager - Dynamic prompts with lazy database loading
"""

from typing import Dict, Any, Optional
from datetime import datetime


class AgentPromptsManager:
    """Manages dynamic agent prompts"""

    def __init__(self):
        self._collection = None
        self.cache: Dict[str, Dict] = {}
        self._initialized = False

    def _get_collection(self):
        """Lazy load collection"""
        if self._collection is None:
            try:
                from db_schema_manager import db

                if db:
                    self._collection = db["agent_prompts"]
            except:
                pass
        return self._collection

    def _initialize_defaults(self):
        """Initialize default prompts"""
        if self._initialized:
            return

        self._initialized = True

        # Default prompts stored in cache
        self.cache = {
            "supervisor_agent": {
                "prompt_template": """You are the Raava Supervisor Agent - intelligent router for the Raava Luxury Automotive Platform.

🎯 YOUR ROLE: Greet customers and route them to specialized agents.

🤖 AVAILABLE AGENTS:
1. AI CONCIERGE - Vehicle buying, finance, bookings
2. AI SERVICE MANAGER - Maintenance and service
3. AI CONSIGNER - Vehicle selling

ROUTING: After understanding need, respond with "ROUTE_TO: [agent_name]"

Always end with: [Replied by: {agent_name}]""",
                "variables": {"agent_name": "Raava Supervisor Agent"},
            },
            "phase1_concierge": {
                "prompt_template": """You are the Raava AI Concierge - luxury automotive acquisition specialist.

💬 FLOW: Greeting → Search → Select → Payment → Details → Create Order

When you have vehicle + payment + customer details, respond:
"CREATE_ORDER_NOW

Vehicle: [details]
Payment: [method]
Customer: [info]"

Always end with: [Replied by: {agent_name}]""",
                "variables": {"agent_name": "Raava AI Concierge"},
            },
        }

    def get_prompt(
        self, agent_name: str, variables: Optional[Dict[str, str]] = None
    ) -> str:
        """Get formatted prompt"""
        self._initialize_defaults()

        if agent_name in self.cache:
            prompt_data = self.cache[agent_name]
        else:
            prompt_data = self._load_from_db(agent_name)
            if prompt_data:
                self.cache[agent_name] = prompt_data
            else:
                return f"Agent prompt not found: {agent_name}"

        template = prompt_data.get("prompt_template", "")
        default_vars = prompt_data.get("variables", {})

        if variables:
            default_vars.update(variables)

        try:
            return template.format(**default_vars)
        except KeyError as e:
            return template

    def save_prompt(self, agent_name: str, prompt_data: Dict[str, Any]) -> bool:
        """Save prompt"""
        self.cache[agent_name] = prompt_data

        col = self._get_collection()
        if col:
            try:
                prompt_data["agent_name"] = agent_name
                prompt_data["last_updated"] = datetime.utcnow()
                col.update_one(
                    {"agent_name": agent_name}, {"$set": prompt_data}, upsert=True
                )
                return True
            except Exception as e:
                print(f"❌ Error saving prompt: {e}")
        return True

    def update_prompt_variables(
        self, agent_name: str, variables: Dict[str, str]
    ) -> bool:
        """Update variables"""
        if agent_name in self.cache:
            if "variables" not in self.cache[agent_name]:
                self.cache[agent_name]["variables"] = {}
            self.cache[agent_name]["variables"].update(variables)
            return self.save_prompt(agent_name, self.cache[agent_name])
        return False

    def get_all_prompts(self) -> Dict[str, Dict]:
        """Get all prompts"""
        self._initialize_defaults()
        return self.cache

    def _load_from_db(self, agent_name: str) -> Optional[Dict]:
        """Load from database"""
        col = self._get_collection()
        if col:
            try:
                doc = col.find_one({"agent_name": agent_name})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as e:
                print(f"❌ Error loading prompt: {e}")
        return None


# Singleton
agent_prompts_manager = AgentPromptsManager()
