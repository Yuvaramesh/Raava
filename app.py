"""
Raava Luxury Automotive Platform - Multi-Agent System
Supervisor Agent routes to:
- Phase 1: AI Concierge (Vehicle Acquisition)
- Phase 2: AI Service Manager (Maintenance & Service)
- Phase 3: AI Consigner (Vehicle Selling)
"""

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
import base64

# Import components
from config import (
    MONGO_CONNECTION_STRING,
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    DB_NAME,
)
from supervisor_agent import supervisor_agent
from phase1_concierge import phase1_concierge
from email_service import email_service
from uk_car_dealers import uk_dealer_aggregator
from uk_finance_calculator import uk_finance_calculator
from order_manager import order_manager

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-in-production")

# MongoDB setup
client = MongoClient(MONGO_CONNECTION_STRING)
db = client[DB_NAME]
cars_collection = db["Cars"]
conversations_collection = db["conversations"]
orders_collection = db["Orders"]
users_collection = db["users"]

# Session storage (in-memory)
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
    Get cars from MongoDB database
    Returns properly formatted car data for frontend
    """
    try:
        # Get filters
        make = request.args.get("make", "")
        search_query = request.args.get("search", "")

        # Build MongoDB query
        query = {}

        if make:
            query["key_information.make"] = {"$regex": make, "$options": "i"}

        if search_query:
            # Search across title and make
            query["$or"] = [
                {"key_information.title": {"$regex": search_query, "$options": "i"}},
                {"key_information.make": {"$regex": search_query, "$options": "i"}},
            ]

        # Fetch from database
        cars_cursor = cars_collection.find(query).limit(50)
        cars = list(cars_cursor)

        # Format cars for frontend
        formatted_cars = []
        for car in cars:
            formatted_cars.append(
                {
                    "_id": str(car["_id"]),
                    "key_information": car.get("key_information", {}),
                    "images": car.get("images", []),
                    "pricing": car.get("pricing", ""),
                    "overview": car.get("overview", ""),
                    "running_costs": car.get("running_costs", ""),
                    "vehicle_history": car.get("vehicle_history", ""),
                    "meet_seller": car.get("meet_seller", ""),
                    "url": car.get("url", ""),
                }
            )

        return jsonify(
            {"success": True, "cars": formatted_cars, "total": len(formatted_cars)}
        )

    except Exception as e:
        print(f"Error in get_cars: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """
    Multi-Agent Chat Endpoint
    Routes through Supervisor Agent to appropriate specialized agent
    """
    try:
        data = request.json
        user_msg = data.get("message", "")
        session_id = data.get("session_id", "default")

        if not user_msg.strip():
            return jsonify(
                {
                    "reply": "Welcome to Raava - the luxury automotive platform. I'm your Supervisor Agent.\n\nI can connect you with our specialized teams:\n\n🚗 **Vehicle Acquisition** - Find and purchase your dream car\n🔧 **Service Management** - Maintain and upgrade your vehicle\n📸 **Vehicle Consignment** - Sell your car with ease\n\nWhich service interests you today?\n\n[Replied by: Raava Supervisor Agent]",
                    "success": True,
                }
            )

        # Get or create session
        if session_id not in user_sessions:
            user_sessions[session_id] = {
                "messages": [],
                "context": {
                    "stage": "supervisor_greeting",
                    "routed": False,
                    "active_agent": None,
                    "preferences": {},
                    "customer_info": {},
                },
            }

        session = user_sessions[session_id]

        # Add user message
        session["messages"].append(HumanMessage(content=user_msg))

        # Prepare state
        state = {
            "messages": session["messages"],
            "context": session["context"],
            "session_id": session_id,
        }

        ai_reply = ""

        # Check if already routed to an agent
        if session["context"].get("routed") and session["context"].get("active_agent"):
            active_agent = session["context"]["active_agent"]

            # Route to appropriate agent
            if active_agent == "phase1_concierge":

                async def get_phase1_response():
                    result = await phase1_concierge.call(state)
                    return result

                result_state = run_async(get_phase1_response())
                ai_reply = result_state["messages"][-1].content

                # Update session context
                session["context"] = result_state.get("context", session["context"])

                # Check if order was created
                if "ORDER CONFIRMED" in ai_reply or "Order ID:" in ai_reply:
                    # Extract order ID and send email
                    import re

                    order_id_match = re.search(r"Order ID:\s*([\w-]+)", ai_reply)
                    if order_id_match:
                        order_id = order_id_match.group(1)
                        # Retrieve full order from database
                        order = orders_collection.find_one({"order_id": order_id})
                        if order:
                            # Send confirmation email
                            email_sent = email_service.send_order_confirmation(order)
                            if email_sent:
                                print(
                                    f"✅ Confirmation email sent for order {order_id}"
                                )
                            else:
                                print(f"⚠️ Failed to send email for order {order_id}")

            elif active_agent == "phase2_service_manager":
                # Phase 2 not implemented yet
                ai_reply = "The Service Manager is currently being prepared. Please check back soon.\n\n[Replied by: Raava Supervisor Agent]"

            elif active_agent == "phase3_consigner":
                # Phase 3 not implemented yet
                ai_reply = "The Consignment Service is currently being prepared. Please check back soon.\n\n[Replied by: Raava Supervisor Agent]"
            else:
                ai_reply = "I encountered an error. Please start a new conversation.\n\n[Replied by: Raava Supervisor Agent]"

        else:
            # Not routed yet - use supervisor agent
            async def get_supervisor_response():
                result = await supervisor_agent.call(state)
                return result

            result_state = run_async(get_supervisor_response())
            ai_reply = result_state["messages"][-1].content

            # Check if routing occurred
            if result_state.get("route_to"):
                session["context"]["routed"] = True
                session["context"]["active_agent"] = result_state["route_to"]

                # Add routing confirmation
                agent_names = {
                    "phase1_concierge": "AI Concierge (Vehicle Acquisition)",
                    "phase2_service_manager": "AI Service Manager",
                    "phase3_consigner": "AI Consigner",
                }
                agent_name = agent_names.get(result_state["route_to"], "Specialist")
                ai_reply += f"\n\n✅ Connected to {agent_name}. How may I assist you?"

        # Update session
        session["messages"].append(AIMessage(content=ai_reply))

        # Save conversation to database
        try:
            conversations_collection.insert_one(
                {
                    "session_id": session_id,
                    "user_message": user_msg,
                    "ai_response": ai_reply,
                    "timestamp": datetime.utcnow(),
                    "active_agent": session["context"].get(
                        "active_agent", "supervisor"
                    ),
                    "stage": session["context"].get("stage", "unknown"),
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
                    "reply": "I apologize for the technical difficulty. Please try rephrasing your question.\n\n[Replied by: Raava Supervisor Agent]",
                    "success": False,
                }
            ),
            500,
        )


@app.route("/api/finance/calculate", methods=["POST"])
def calculate_finance():
    """Calculate finance options for a vehicle"""
    try:
        data = request.json
        vehicle_price = data.get("vehicle_price")
        deposit_percent = data.get("deposit_percent", 10)
        term_months = data.get("term_months", 48)
        credit_score = data.get("credit_score", "Good")

        if not vehicle_price:
            return jsonify({"success": False, "message": "vehicle_price required"}), 400

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


@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    """Get order details by order ID"""
    try:
        order = order_manager.get_order(order_id)

        if order:
            return jsonify({"success": True, "order": order})
        else:
            return jsonify({"success": False, "message": "Order not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/orders/customer/<email>", methods=["GET"])
def get_customer_orders(email):
    """Get all orders for a customer by email"""
    try:
        orders = order_manager.get_customer_orders(email)
        return jsonify({"success": True, "orders": orders, "count": len(orders)})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        db.command("ping")
        db_status = "connected"
        car_count = cars_collection.count_documents({})
        order_count = orders_collection.count_documents({})
        conversation_count = conversations_collection.count_documents({})
    except Exception as e:
        db_status = f"error: {str(e)}"
        car_count = 0
        order_count = 0
        conversation_count = 0

    return jsonify(
        {
            "status": "healthy",
            "service": "Raava Multi-Agent Platform",
            "database": {
                "status": db_status,
                "name": DB_NAME,
                "cars": car_count,
                "orders": order_count,
                "conversations": conversation_count,
            },
            "agents": {
                "supervisor": "active",
                "phase1_concierge": "active - Vehicle Acquisition",
                "phase2_service_manager": "in_development - Service & Maintenance",
                "phase3_consigner": "in_development - Vehicle Consignment",
            },
            "features": [
                "✅ Supervisor Agent Routing",
                "✅ Phase 1: AI Concierge (Acquisition)",
                "✅ Marketplace Aggregation",
                "✅ Finance Assessment (5 UK providers)",
                "✅ Order Management",
                "✅ Email Confirmations",
                "✅ Voice Synthesis",
                "🚧 Phase 2: Service Manager",
                "🚧 Phase 3: Consigner",
            ],
        }
    )


if __name__ == "__main__":
    print("🚗 Raava Luxury Automotive Platform - Multi-Agent System")
    print("=" * 70)
    print("Supervisor Agent: Active")
    print("  └─ Routes to specialized agents based on user intent")
    print("\nActive Agents:")
    print("  ✅ Phase 1: AI Concierge (Vehicle Acquisition)")
    print("     • Vehicle search & recommendations")
    print("     • Finance calculations")
    print("     • Purchase, rental, booking orders")
    print("     • Email confirmations")
    print("\nIn Development:")
    print("  🚧 Phase 2: AI Service Manager (Maintenance)")
    print("  🚧 Phase 3: AI Consigner (Vehicle Selling)")
    print("=" * 70)
    app.run(debug=True, host="0.0.0.0", port=5000)
