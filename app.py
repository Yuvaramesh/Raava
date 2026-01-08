"""
Raava Enhanced App - With Session Management & Email
Works with existing codebase, adds new features
"""

from flask import Flask, render_template, request, jsonify, session as flask_session
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# Import from existing files
from config import MONGO_CONNECTION_STRING, DB_NAME
from db_schema_manager import (
    db,
    cars_collection,
    orders_collection,
    conversations_collection,
)
from supervisor_agent import supervisor_agent
from phase1_concierge import phase1_concierge
from order_manager import order_manager
from uk_finance_calculator import uk_finance_calculator

# Import new enhanced features
from session_manager import session_manager
from agent_prompts_manager import agent_prompts_manager
from db_schema_manager import db_schema_manager
from enhanced_email_service import enhanced_email_service

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-in-production")


def run_async(coro):
    """Run async function"""
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
    if "session_id" not in flask_session:
        flask_session["session_id"] = str(uuid.uuid4())
    return render_template("chat.html")


@app.route("/api/cars", methods=["GET"])
def get_cars():
    """Get cars"""
    try:
        make = request.args.get("make", "")
        query = {}
        if make:
            query["make"] = {"$regex": make, "$options": "i"}

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
                }
            )

        return jsonify({"success": True, "cars": formatted_cars})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat with session management"""
    try:
        data = request.json
        user_msg = data.get("message", "")
        session_id = (
            data.get("session_id")
            or flask_session.get("session_id")
            or str(uuid.uuid4())
        )

        if not user_msg.strip():
            return jsonify(
                {
                    "reply": "Welcome to Raava! How can I assist you today?",
                    "success": True,
                    "session_id": session_id,
                }
            )

        # Get or create session using new session manager
        session_state = session_manager.get_session(session_id)

        print(f"\n📍 Session: {session_id}")
        print(f"📍 Stage: {session_state.stage}")

        # Prepare messages
        messages = []
        for turn in session_state.conversation_history[-5:]:
            messages.append(HumanMessage(content=turn["user_message"]))
            messages.append(AIMessage(content=turn["ai_response"]))
        messages.append(HumanMessage(content=user_msg))

        # Prepare state
        state = {
            "messages": messages,
            "context": {
                "stage": session_state.stage,
                "routed": session_state.routed,
                "active_agent": session_state.active_agent,
                "preferences": session_state.preferences,
                "customer_info": session_state.customer_info,
                "payment_method": session_state.payment_method,
                "finance_type": session_state.finance_type,
                "selected_vehicle": session_state.selected_vehicle,
                "available_vehicles": session_state.available_vehicles,
                "order_created": session_state.order_created,
                "order_id": session_state.order_id,
            },
            "session_id": session_id,
        }

        ai_reply = ""
        order_created = False
        order_id = None

        # Route to agent
        if session_state.routed and session_state.active_agent:
            if session_state.active_agent == "phase1_concierge":
                result_state = run_async(phase1_concierge.call(state))
                ai_reply = result_state["messages"][-1].content

                # Update session
                returned_context = result_state.get("context", {})
                session_manager.update_session(
                    session_id,
                    {
                        "stage": returned_context.get("stage", session_state.stage),
                        "payment_method": returned_context.get("payment_method"),
                        "finance_type": returned_context.get("finance_type"),
                        "selected_vehicle": returned_context.get("selected_vehicle"),
                        "available_vehicles": returned_context.get(
                            "available_vehicles"
                        ),
                        "customer_info": returned_context.get("customer_info", {}),
                        "order_created": returned_context.get("order_created", False),
                        "order_id": returned_context.get("order_id"),
                    },
                )

                # Check for order
                if returned_context.get("order_created"):
                    order_id = returned_context.get("order_id")
                    order_created = True

                    # Send email
                    db_order = orders_collection.find_one({"order_id": order_id})
                    if db_order:
                        enhanced_email_service.send_order_confirmation(db_order)

            else:
                ai_reply = "Agent in development"
        else:
            # Use supervisor
            result_state = run_async(supervisor_agent.call(state))
            ai_reply = result_state["messages"][-1].content

            if result_state.get("route_to"):
                session_manager.update_session(
                    session_id,
                    {
                        "routed": True,
                        "active_agent": result_state["route_to"],
                    },
                )

        # Add conversation turn
        session_manager.add_conversation_turn(
            session_id,
            user_msg,
            ai_reply,
            metadata={"order_created": order_created, "order_id": order_id},
        )

        response_data = {
            "reply": ai_reply,
            "success": True,
            "session_id": session_id,
            "order_created": order_created,
        }

        if order_created:
            response_data["order_id"] = order_id
            response_data["session_ended"] = True
            session_manager.end_session(session_id)
            response_data["reply"] += "\n\n✅ Session Complete!"

        return jsonify(response_data)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return (
            jsonify(
                {"reply": "Technical difficulty. Please try again.", "success": False}
            ),
            500,
        )


@app.route("/api/session/<session_id>", methods=["GET"])
def get_session_info(session_id):
    """Get session info"""
    summary = session_manager.get_session_summary(session_id)
    if summary:
        return jsonify({"success": True, "session": summary})
    return jsonify({"success": False}), 404


@app.route("/api/orders", methods=["GET"])
def get_all_orders():
    """Get orders"""
    try:
        orders = list(orders_collection.find().sort("created_at", -1).limit(50))
        for order in orders:
            order["_id"] = str(order["_id"])
            if isinstance(order.get("created_at"), datetime):
                order["created_at"] = order["created_at"].isoformat()
        return jsonify({"success": True, "orders": orders})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check"""
    try:
        db.command("ping")
        db_status = "connected"
        car_count = cars_collection.count_documents({})
        order_count = orders_collection.count_documents({})
    except:
        db_status = "error"
        car_count = 0
        order_count = 0

    return jsonify(
        {
            "status": "healthy",
            "service": "Raava Enhanced Platform",
            "database": {
                "status": db_status,
                "cars": car_count,
                "orders": order_count,
            },
            "features": {
                "session_management": "✅ Active",
                "email_service": f"✅ Active ({enhanced_email_service.config.email_enabled})",
                "dynamic_prompts": "✅ Active",
            },
        }
    )


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚗 RAAVA ENHANCED PLATFORM")
    print("=" * 70)
    print("✅ Session Management with Memory")
    print("✅ Enhanced Email Service")
    print("✅ Dynamic Configuration")
    print("=" * 70 + "\n")

    session_manager.cleanup_expired_sessions()

    app.run(debug=True, host="0.0.0.0", port=5000)
