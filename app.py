"""
Raava App.py - FIXED ORDER STORAGE
Ensures orders are saved to Orders collection
"""

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
import base64
import re

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
orders_collection = db["Orders"]  # ✅ ORDERS COLLECTION
users_collection = db["users"]

# Session storage
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
    return render_template("index.html")


@app.route("/chat-page")
def chat_page():
    return render_template("chat.html")


@app.route("/api/cars", methods=["GET"])
def get_cars():
    """Get cars from MongoDB"""
    try:
        make = request.args.get("make", "")
        search_query = request.args.get("search", "")

        query = {}
        if make:
            query["make"] = {"$regex": make, "$options": "i"}
        if search_query:
            query["$or"] = [
                {"make": {"$regex": search_query, "$options": "i"}},
                {"model": {"$regex": search_query, "$options": "i"}},
            ]

        cars = list(cars_collection.find(query).limit(50))

        formatted_cars = []
        for car in cars:
            formatted_cars.append(
                {
                    "_id": str(car["_id"]),
                    "make": car.get("make", ""),
                    "model": car.get("model", ""),
                    "year": car.get("year", ""),
                    "price": car.get("price", 0),
                    "mileage": car.get("mileage", 0),
                    "images": car.get("images", []),
                }
            )

        return jsonify(
            {"success": True, "cars": formatted_cars, "total": len(formatted_cars)}
        )

    except Exception as e:
        print(f"Error in get_cars: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """
    FIXED Multi-Agent Chat with Proper Order Storage
    """
    try:
        data = request.json
        user_msg = data.get("message", "")
        session_id = data.get("session_id", "default")

        if not user_msg.strip():
            return jsonify(
                {
                    "reply": "Welcome to Raava! How can I assist you today?",
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
                    "payment_method": None,
                    "finance_type": None,
                    "selected_vehicle": None,
                    "available_vehicles": [],
                },
            }

        print(f"\n📍 Session: {session_id}")
        print(f"📍 Stage BEFORE: {user_sessions[session_id]['context'].get('stage')}")
        print(f"📍 Routed: {user_sessions[session_id]['context'].get('routed')}")
        print(
            f"📍 Active Agent: {user_sessions[session_id]['context'].get('active_agent')}"
        )

        session = user_sessions[session_id]
        session["messages"].append(HumanMessage(content=user_msg))

        # Prepare state
        state = {
            "messages": session["messages"],
            "context": session["context"],
            "session_id": session_id,
        }

        ai_reply = ""
        order_created = False
        order_id = None

        # Route to appropriate agent
        if session["context"].get("routed") and session["context"].get("active_agent"):
            active_agent = session["context"]["active_agent"]

            if active_agent == "phase1_concierge":
                # Call Phase 1 Concierge
                async def get_phase1_response():
                    result = await phase1_concierge.call(state)
                    return result

                result_state = run_async(get_phase1_response())
                ai_reply = result_state["messages"][-1].content

                # ✅ CRITICAL: Update session context with returned context
                session["context"].update(result_state.get("context", {}))

                print(f"\n📍 Stage AFTER: {session['context'].get('stage')}")
                print(
                    f"📍 Has Vehicle: {bool(session['context'].get('selected_vehicle'))}"
                )
                print(f"📍 Payment: {session['context'].get('payment_method')}")

                # 🔥 CHECK IF ORDER WAS CREATED
                print(f"\n🔍 Checking for order creation...")
                print(
                    f"   Context order_created: {session['context'].get('order_created')}"
                )
                print(f"   Context order_id: {session['context'].get('order_id')}")

                # Check if order was created in context
                if session["context"].get("order_created") and session["context"].get(
                    "order_id"
                ):
                    order_id = session["context"]["order_id"]
                    order_created = True
                    print(f"✅ ORDER DETECTED IN CONTEXT: {order_id}")

                    # Verify in database
                    db_order = orders_collection.find_one({"order_id": order_id})
                    if db_order:
                        print(f"✅ ORDER VERIFIED IN DATABASE: {order_id}")

                        # Send email
                        email_sent = email_service.send_order_confirmation(db_order)
                        if email_sent:
                            print(f"✅ Email sent for order {order_id}")
                    else:
                        print(f"❌ ORDER NOT FOUND IN DATABASE: {order_id}")

                # Also check response text for order confirmation
                elif "ORDER CONFIRMED" in ai_reply or "Order ID:" in ai_reply:
                    print("🔍 Found order confirmation in response text")
                    order_match = re.search(r"Order ID:\s*([\w-]+)", ai_reply)
                    if order_match:
                        order_id = order_match.group(1)
                        order_created = True
                        print(f"✅ Extracted order ID from text: {order_id}")

                        # Verify in database
                        db_order = orders_collection.find_one({"order_id": order_id})
                        if db_order:
                            print(f"✅ ORDER FOUND IN DATABASE")
                            email_service.send_order_confirmation(db_order)
                        else:
                            print(f"❌ ORDER NOT IN DATABASE")

            elif active_agent == "phase2_service_manager":
                ai_reply = "Service Manager coming soon."
            elif active_agent == "phase3_consigner":
                ai_reply = "Consignment Service coming soon."
            else:
                ai_reply = "Error - please start new conversation."

        else:
            # Not routed - use supervisor
            async def get_supervisor_response():
                result = await supervisor_agent.call(state)
                return result

            result_state = run_async(get_supervisor_response())
            ai_reply = result_state["messages"][-1].content

            # Check routing
            if result_state.get("route_to"):
                session["context"]["routed"] = True
                session["context"]["active_agent"] = result_state["route_to"]

                agent_names = {
                    "phase1_concierge": "AI Concierge (Vehicle Acquisition)",
                    "phase2_service_manager": "AI Service Manager",
                    "phase3_consigner": "AI Consigner",
                }
                agent_name = agent_names.get(result_state["route_to"], "Specialist")
                ai_reply += f"\n\n✅ Connected to {agent_name}."

        # Update session
        session["messages"].append(AIMessage(content=ai_reply))

        # 🔥 SAVE CONVERSATION TO DATABASE
        try:
            conversation_doc = {
                "session_id": session_id,
                "user_message": user_msg,
                "ai_response": ai_reply,
                "timestamp": datetime.utcnow(),
                "active_agent": session["context"].get("active_agent", "supervisor"),
                "stage": session["context"].get("stage", "unknown"),
                "order_created": order_created,
                "order_id": order_id if order_created else None,
            }

            conversations_collection.insert_one(conversation_doc)
            print(f"✅ Conversation saved to database")

        except Exception as db_error:
            print(f"❌ Failed to save conversation: {db_error}")

        # Prepare response
        response_data = {
            "reply": ai_reply,
            "success": True,
            "session_id": session_id,
            "order_created": order_created,
        }

        if order_created:
            response_data["order_id"] = order_id
            response_data["session_ended"] = True

            # Clear session after order
            if session_id in user_sessions:
                del user_sessions[session_id]
                print(f"✅ Session {session_id} cleared")

            response_data[
                "reply"
            ] += "\n\n---\n\n✅ **Session Complete**\n\nYour order has been confirmed. Thank you for choosing Raava! 🚗✨"

        return jsonify(response_data)

    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback

        traceback.print_exc()

        return (
            jsonify(
                {
                    "reply": "I apologize for the technical difficulty. Please try again.",
                    "success": False,
                }
            ),
            500,
        )


@app.route("/api/finance/calculate", methods=["POST"])
def calculate_finance():
    """Calculate finance options"""
    try:
        data = request.json
        vehicle_price = data.get("vehicle_price")

        if not vehicle_price:
            return jsonify({"success": False, "message": "vehicle_price required"}), 400

        options = uk_finance_calculator.calculate_all_options(
            vehicle_price=float(vehicle_price),
            deposit_percent=10,
            term_months=48,
            credit_score="Good",
        )

        return jsonify({"success": True, "finance_options": options})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    """Get order by ID"""
    try:
        order = orders_collection.find_one({"order_id": order_id})

        if order:
            order["_id"] = str(order["_id"])
            return jsonify({"success": True, "order": order})
        else:
            return jsonify({"success": False, "message": "Order not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/orders", methods=["GET"])
def get_all_orders():
    """Get all orders from Orders collection"""
    try:
        orders = list(orders_collection.find().sort("created_at", -1).limit(50))

        for order in orders:
            order["_id"] = str(order["_id"])

            # Convert datetime to string
            if "created_at" in order and isinstance(order["created_at"], datetime):
                order["created_at"] = order["created_at"].isoformat()
            if "updated_at" in order and isinstance(order["updated_at"], datetime):
                order["updated_at"] = order["updated_at"].isoformat()

        return jsonify({"success": True, "orders": orders, "count": len(orders)})

    except Exception as e:
        print(f"Error getting orders: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check"""
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
                "phase1_concierge": "active - FIXED ORDER CREATION",
                "phase2_service_manager": "in_development",
                "phase3_consigner": "in_development",
            },
            "features": [
                "✅ Supervisor Agent Routing",
                "✅ Phase 1: AI Concierge (FIXED)",
                "✅ Payment Method Selection (Cash/Finance)",
                "✅ Finance Type Selection (PCP/HP/Lease)",
                "✅ Order Storage in Orders Collection",
                "✅ Email Confirmations",
                "🚧 Phase 2: Service Manager",
                "🚧 Phase 3: Consigner",
            ],
        }
    )


if __name__ == "__main__":
    print("🚗 Raava Platform - FIXED ORDER STORAGE")
    print("=" * 70)
    print("✅ Orders now properly save to 'Orders' collection")
    print("✅ Payment method selection (Cash/Finance)")
    print("✅ Finance type selection (PCP/HP/Lease)")
    print("=" * 70)
    app.run(debug=True, host="0.0.0.0", port=5000)
