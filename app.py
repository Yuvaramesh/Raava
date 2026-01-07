"""
Raava Luxury Automotive Platform - Integrated Application
Phase 1: Marketplace Aggregation + Finance Assessment
"""

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
import base64

# Import Phase 1 components
from config import MONGO_URI, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
from phase1_concierge import phase1_concierge
from uk_car_dealers import uk_dealer_aggregator
from uk_finance_calculator import uk_finance_calculator

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-in-production")

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client["Raava_Sales"]
cars_collection = db["Cars"]
conversations_collection = db["conversations"]
orders_collection = db["orders"]

# Session storage (in-memory for demo, use Redis in production)
user_sessions = {}


def run_async(coro):
    """Run async function in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@app.route("/")
def home():
    """Landing page with marketplace integration"""
    return render_template("index.html")


@app.route("/chat-page")
def chat_page():
    """AI Concierge chat interface"""
    return render_template("chat.html")


@app.route("/api/cars", methods=["GET"])
def get_cars():
    """
    Get cars from multiple sources
    - Local database (Raava exclusive inventory)
    - AutoTrader
    - Motors.co.uk
    - CarGurus
    - PistonHeads
    """
    try:
        # Get filters
        make = request.args.get("make", "")
        model = request.args.get("model", "")
        price_min = request.args.get("price_min", type=int)
        price_max = request.args.get("price_max", type=int)

        # Search local database
        local_query = {}
        if make:
            local_query["make"] = {"$regex": make, "$options": "i"}
        if model:
            local_query["model"] = {"$regex": model, "$options": "i"}

        local_cars = list(cars_collection.find(local_query).limit(20))

        # Format local cars
        formatted_local = []
        for car in local_cars:
            car["_id"] = str(car["_id"])
            car["source"] = "Raava Exclusive"
            formatted_local.append(car)

        # Search UK dealers
        uk_cars = uk_dealer_aggregator.search_luxury_cars(
            make=make if make else None,
            model=model if model else None,
            price_min=price_min if price_min else 30000,
            price_max=price_max if price_max else None,
            limit=30,
        )

        # Combine results
        all_cars = formatted_local + uk_cars

        return jsonify(
            {
                "success": True,
                "cars": all_cars,
                "total": len(all_cars),
                "sources": {
                    "raava_exclusive": len(formatted_local),
                    "uk_dealers": len(uk_cars),
                },
            }
        )

    except Exception as e:
        print(f"Error in get_cars: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/finance/calculate", methods=["POST"])
def calculate_finance():
    """
    Calculate finance options for a vehicle
    Returns PCP, HP, and Lease options from multiple UK providers
    """
    try:
        data = request.json
        vehicle_price = data.get("vehicle_price")
        deposit_percent = data.get("deposit_percent", 10)
        term_months = data.get("term_months", 48)
        credit_score = data.get("credit_score", "Good")

        if not vehicle_price:
            return jsonify({"success": False, "message": "vehicle_price required"}), 400

        # Calculate options
        options = uk_finance_calculator.calculate_all_options(
            vehicle_price=float(vehicle_price),
            deposit_percent=float(deposit_percent),
            term_months=int(term_months),
            credit_score=credit_score,
        )

        return jsonify({"success": True, "finance_options": options})

    except Exception as e:
        print(f"Error in calculate_finance: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """
    AI Concierge chat endpoint
    Phase 1 Features:
    - Marketplace aggregation
    - Finance assessment
    - Buyer-seller facilitation
    """
    try:
        data = request.json
        user_msg = data.get("message", "")
        session_id = data.get("session_id", "default")

        if not user_msg.strip():
            return jsonify(
                {
                    "reply": "I'm here to assist you with luxury automotive acquisition. How may I help you today?",
                    "success": True,
                }
            )

        # Get or create session
        if session_id not in user_sessions:
            user_sessions[session_id] = {"messages": []}

        session = user_sessions[session_id]

        # Add user message
        session["messages"].append(HumanMessage(content=user_msg))

        # Prepare state for concierge
        state = {"messages": session["messages"]}

        # Get response from Phase 1 Concierge
        async def get_concierge_response():
            result = await phase1_concierge.call(state)
            return result["messages"][-1].content

        ai_reply = run_async(get_concierge_response())

        # Add AI response to session
        session["messages"].append(AIMessage(content=ai_reply))

        # Save conversation to database
        try:
            conversations_collection.insert_one(
                {
                    "session_id": session_id,
                    "user_message": user_msg,
                    "ai_response": ai_reply,
                    "timestamp": os.time.time(),
                }
            )
        except Exception as db_error:
            print(f"DB save error: {db_error}")

        return jsonify({"reply": ai_reply, "success": True, "session_id": session_id})

    except Exception as e:
        print(f"Chat error: {e}")
        import traceback

        traceback.print_exc()

        return (
            jsonify(
                {
                    "reply": "I apologize for the technical difficulty. Please try rephrasing your question.",
                    "success": False,
                }
            ),
            500,
        )


@app.route("/api/marketplace/search", methods=["POST"])
def marketplace_search():
    """
    Direct marketplace search endpoint
    Search across all connected UK platforms
    """
    try:
        data = request.json
        make = data.get("make")
        model = data.get("model")
        price_min = data.get("price_min", 30000)
        price_max = data.get("price_max")

        results = uk_dealer_aggregator.search_luxury_cars(
            make=make, model=model, price_min=price_min, price_max=price_max, limit=20
        )

        return jsonify({"success": True, "results": results, "count": len(results)})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/text-to-speech", methods=["POST"])
def text_to_speech():
    """Convert text to speech using ElevenLabs"""
    try:
        data = request.json
        text = data.get("text", "")

        if not text:
            return jsonify({"success": False, "message": "No text provided"}), 400

        if not ELEVENLABS_API_KEY:
            return jsonify({"success": False, "message": "TTS not configured"}), 500

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

        import requests

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            audio_base64 = base64.b64encode(response.content).decode("utf-8")
            return jsonify({"success": True, "audio": audio_base64})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"ElevenLabs error: {response.status_code}",
                    }
                ),
                500,
            )

    except Exception as e:
        print(f"TTS error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "Raava Phase 1 - AI Concierge",
            "features": [
                "Marketplace Aggregation (AutoTrader, Motors, CarGurus, PistonHeads)",
                "Finance Assessment (Zuto, Santander, Black Horse, Close Brothers, MotoNovo)",
                "AI Concierge Chat",
                "Voice Synthesis",
            ],
        }
    )


if __name__ == "__main__":
    print("🚗 Raava Luxury Automotive Platform - Phase 1")
    print("=" * 60)
    print("Features Enabled:")
    print("  ✓ Multi-marketplace aggregation")
    print("  ✓ UK finance calculator (5 providers)")
    print("  ✓ AI Concierge (OpenAI GPT-5)")
    print("  ✓ Voice synthesis")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
