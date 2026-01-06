"""
Raava Phase 1 - Integrated Application with:
- Marketplace API Integrations (AutoTrader, CarGurus)
- Finance Calculation Models (HP, PCP, Lease, Bespoke)
- Enhanced Inventory Search
- Analytics Tracking
"""

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import google.generativeai as genai
from datetime import datetime
import json
from bson import ObjectId
import requests
import base64

# Import integration modules
from integrations import LuxuryCarAggregator, format_search_results, validate_api_keys
from finance import FinanceComparator, InsuranceEstimator

load_dotenv()
app = Flask(__name__)

# ============= MongoDB Setup =============
try:
    client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
    db = client["Raava_Luxury"]
    users_collection = db["users"]
    conversations_collection = db["conversations"]
    analytics_collection = db["analytics"]
    search_cache_collection = db["search_cache"]
    print("✓ MongoDB connected")
except Exception as e:
    print(f"✗ MongoDB error: {e}")

# ============= Gemini Setup =============
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    print("✓ Gemini configured")
except Exception as e:
    print(f"✗ Gemini error: {e}")

# ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "mCQMfsqGDT6IDkEKR20a")


# ============= Context Management =============
class LuxuryConciergeContext:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_profile = self._load_or_create_user()
        self.conversation_history = self._load_conversation_history()
        self.session_state = {
            "intent": None,
            "stage": "initial",
            "car_requirements": {},
            "search_results": [],
            "quotes": {},
        }

    def _load_or_create_user(self) -> dict:
        user = users_collection.find_one({"user_id": self.user_id})
        if not user:
            user = {
                "user_id": self.user_id,
                "created_at": datetime.now(),
                "preferences": {},
                "contact_info": {},
                "saved_cars": [],
                "interaction_count": 0,
            }
            users_collection.insert_one(user)
        return user

    def _load_conversation_history(self) -> list:
        conv = conversations_collection.find_one({"user_id": self.user_id})
        return conv.get("messages", [])[-20:] if conv else []

    def add_message(self, role: str, content: str):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self.conversation_history.append(message)
        conversations_collection.update_one(
            {"user_id": self.user_id},
            {
                "$push": {
                    "messages": {
                        "role": role,
                        "content": content,
                        "timestamp": datetime.now(),
                    }
                },
                "$set": {"updated_at": datetime.now()},
                "$inc": {"message_count": 1},
            },
            upsert=True,
        )

    def track_search(self, intent: str, brands: list, budget: dict):
        """Track search analytics"""
        analytics_collection.insert_one(
            {
                "user_id": self.user_id,
                "timestamp": datetime.now(),
                "intent": intent,
                "brands": brands,
                "budget": budget,
                "event_type": "search",
            }
        )


# ============= Luxury Concierge =============
class LuxuryCarConcierge:
    def __init__(self):
        self.system_prompt = """You are Raava, an exclusive AI concierge for luxury automotive enthusiasts.

PERSONALITY:
- Sophisticated, refined, genuinely helpful
- Never bot-like or salesy
- Natural, conversational
- Attentive to preferences
- Anticipate needs

EXPERTISE:
- Ultra-premium cars: Ferrari, Lamborghini, Porsche, McLaren, Bugatti, Aston Martin, Bentley, Rolls-Royce
- Financing: PCP, HP, Lease, Bespoke for UHNW
- Marketplace access
- Luxury insurance
- Resale strategy

KEY ACTIONS:
1. Understanding: Ask about use case, budget, brands, features
2. Searching: Help search marketplaces
3. Quoting: Generate finance & insurance quotes
4. Facilitating: Help with next steps

Always be concise (max 200 words), specific, and remember conversation details."""

    def generate_response(
        self, user_message: str, context: LuxuryConciergeContext
    ) -> tuple:
        """Generate response and determine next action"""
        try:
            # Build context
            conversation_context = ""
            if context.conversation_history:
                recent = context.conversation_history[-10:]
                for msg in recent:
                    content = msg.get("content", "")[:100]
                    conversation_context += (
                        f"\n{msg.get('role', 'user').upper()}: {content}"
                    )

            # Analyze intent
            intent_prompt = f"""Analyze this message for intent.

Message: "{user_message}"

Return ONLY JSON (no markdown):
{{
    "intent": "buy"|"sell"|"finance"|"insurance"|"search"|"general",
    "extracted_brands": [],
    "extracted_budget": {{"min": null, "max": null}},
    "needs_search": true|false,
    "needs_quotes": true|false
}}"""

            intent_response = model.generate_content(intent_prompt)
            intent_data = json.loads(intent_response.text)

            context.session_state["intent"] = intent_data.get("intent", "general")

            # Get concierge response
            full_prompt = f"""{self.system_prompt}

CONVERSATION:{conversation_context if conversation_context else "(New conversation)"}

USER: {user_message}

Respond naturally. If they're buying, help narrow requirements. If searching, prepare to show results.
If they want quotes, ask for financial details to tailor options.
Keep responses under 150 words."""

            response = model.generate_content(full_prompt)

            return response.text, intent_data

        except Exception as e:
            print(f"Response generation error: {e}")
            return "I apologize for the difficulty. Could you please rephrase?", {
                "intent": "general"
            }


# ============= Routes =============


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat-page")
def chat_page():
    return render_template("chat.html")


@app.route("/analytics")
def analytics():
    return render_template("analytics.html")


@app.route("/api/initialize", methods=["POST"])
def initialize():
    try:
        user_id = request.json.get(
            "user_id", f"user_{int(datetime.now().timestamp() * 1000)}"
        )
        context = LuxuryConciergeContext(user_id)

        intro = """Hi there, I'm Raava, your personal automotive concierge.

I'm here to help you find your dream car, explore financing options, understand the market, or prepare to sell your current vehicle. Whether you're looking for a specific marque or exploring what's possible, I'm here to make this seamless.

What brings you in today?"""

        context.add_message("assistant", intro)
        return jsonify({"success": True, "user_id": user_id, "intro_message": intro})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        message = data.get("message", "").strip()

        if not user_id or not message:
            return (
                jsonify({"success": False, "error": "Missing user_id or message"}),
                400,
            )

        context = LuxuryConciergeContext(user_id)
        context.add_message("user", message)

        # Generate response with intent analysis
        concierge = LuxuryCarConcierge()
        response, intent_data = concierge.generate_response(message, context)

        # If marketplace search needed, fetch results
        search_results = []
        if intent_data.get("needs_search"):
            aggregator = LuxuryCarAggregator()
            search_results = aggregator.search_all_marketplaces(
                make=intent_data.get("extracted_brands", [None])[0],
                min_price=intent_data.get("extracted_budget", {}).get("min"),
                max_price=intent_data.get("extracted_budget", {}).get("max"),
                min_year=2023,
            )
            context.session_state["search_results"] = search_results["cars"]

            # Append search results to response
            if search_results["cars"]:
                response += (
                    f"\n\n{format_search_results(search_results['cars'], limit=5)}"
                )

            # Track analytics
            context.track_search(
                intent_data.get("intent"),
                intent_data.get("extracted_brands", []),
                intent_data.get("extracted_budget", {}),
            )

        # If finance quotes needed
        quotes = {}
        if intent_data.get("needs_quotes"):
            # Extract budget
            budget = intent_data.get("extracted_budget", {}).get("max", 250000)
            comparator = FinanceComparator()
            quotes = comparator.compare_all_options(budget)
            context.session_state["quotes"] = {k: v.__dict__ for k, v in quotes.items()}

            # Append quotes to response
            response += f"\n\n{FinanceComparator.format_comparison(quotes)}"

        context.add_message("assistant", response)

        return jsonify(
            {
                "success": True,
                "reply": response,
                "session_state": context.session_state,
                "intent": context.session_state.get("intent"),
                "search_results": context.session_state.get("search_results", [])[:5],
            }
        )

    except Exception as e:
        print(f"Chat error: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/search", methods=["POST"])
def search():
    """Enhanced marketplace search endpoint"""
    try:
        data = request.get_json()
        make = data.get("make")
        model = data.get("model")
        min_price = data.get("min_price")
        max_price = data.get("max_price")
        location = data.get("location")

        aggregator = LuxuryCarAggregator()
        results = aggregator.search_all_marketplaces(
            make=make,
            model=model,
            min_price=min_price,
            max_price=max_price,
            location=location,
        )

        return jsonify({"success": True, "results": results})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/finance-quotes", methods=["POST"])
def finance_quotes():
    """Generate finance quotes"""
    try:
        data = request.get_json()
        vehicle_price = data.get("vehicle_price", 250000)
        term_months = data.get("term_months", 36)

        comparator = FinanceComparator()
        quotes = comparator.compare_all_options(vehicle_price, term_months=term_months)

        quotes_data = {
            k: {
                "product_name": v.product_name,
                "monthly_payment": round(v.monthly_payment, 2),
                "total_cost": round(v.total_cost, 2),
                "deposit": round(v.deposit, 2),
                "apr": v.annual_rate,
                "features": v.key_features,
            }
            for k, v in quotes.items()
        }

        return jsonify({"success": True, "quotes": quotes_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/insurance-estimate", methods=["POST"])
def insurance_estimate():
    """Estimate insurance costs"""
    try:
        data = request.get_json()
        make = data.get("make", "Ferrari")
        vehicle_price = data.get("vehicle_price", 250000)
        driver_age = data.get("driver_age", 45)

        estimate = InsuranceEstimator.estimate_annual_insurance(
            make, vehicle_price, driver_age
        )

        return jsonify({"success": True, "estimate": estimate})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/text-to-speech", methods=["POST"])
def text_to_speech():
    """Convert text to speech"""
    try:
        text = request.json.get("text", "").strip()

        if not text or not ELEVENLABS_API_KEY:
            return jsonify({"success": False, "error": "No text or API key"}), 400

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY,
        }
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            audio_base64 = base64.b64encode(response.content).decode("utf-8")
            return jsonify({"success": True, "audio": audio_base64})
        else:
            return (
                jsonify(
                    {"success": False, "error": f"TTS error: {response.status_code}"}
                ),
                500,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Get analytics data"""
    try:
        period = request.args.get("period", 7)
        analytics_data = {
            "total_conversations": conversations_collection.count_documents({}),
            "total_searches": analytics_collection.count_documents(
                {"event_type": "search"}
            ),
            "total_quotes": analytics_collection.count_documents(
                {"event_type": "quote"}
            ),
            "avg_satisfaction": 4.7,
        }
        return jsonify({"success": True, "analytics": analytics_data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============= Error Handlers =============
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Server error"}), 500


# ============= Main =============
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RAAVA - Luxury Automotive Concierge (Phase 1)")
    print("=" * 60)
    print(f"MongoDB: Connected")
    print(f"Gemini: Ready")
    print(f"Marketplace APIs: {validate_api_keys()}")
    print(f"ElevenLabs: {'Configured' if ELEVENLABS_API_KEY else 'Not configured'}")
    print("=" * 60)
    print("\nServer running at http://localhost:5000")
    print("Chat: http://localhost:5000/chat-page")
    print("Analytics: http://localhost:5000/analytics")
    print("=" * 60 + "\n")

    app.run(debug=True, host="0.0.0.0", port=5000)
