"""
Raava Enhanced App - With Phase 2 Service Manager
Complete integration of all phases
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

# Import agents
from supervisor_agent import supervisor_agent
from phase1_concierge import phase1_concierge
from phase2_service_manager import phase2_service_manager

# Import managers
from order_manager import order_manager
from uk_finance_calculator import uk_finance_calculator
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
    """Enhanced chat with PROPER session clearing after appointments/orders"""
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

        # Get or create session
        session_state = session_manager.get_session(session_id)

        print(f"\n📋 Session: {session_id}")
        print(f"📊 Stage: {session_state.stage}")
        print(f"🤖 Active Agent: {session_state.active_agent}")

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
                "session_id": session_id,  # Add session_id to context
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
                # Phase 2 specific context
                "service_stage": session_state.metadata.get("service_stage"),
                "vehicle_info": session_state.metadata.get("vehicle_info", {}),
                "service_request": session_state.metadata.get("service_request", {}),
                "customer_service_info": session_state.metadata.get(
                    "customer_service_info", {}
                ),
                "selected_provider": session_state.metadata.get("selected_provider"),
                "appointment_date": session_state.metadata.get("appointment_date"),
                "appointment_created": session_state.metadata.get(
                    "appointment_created", False
                ),
                "appointment_id": session_state.metadata.get("appointment_id"),
            },
            "session_id": session_id,
        }

        ai_reply = ""
        order_created = False
        order_id = None
        appointment_created = False
        appointment_id = None

        # Route to appropriate agent
        if session_state.routed and session_state.active_agent:
            if session_state.active_agent == "phase1_concierge":
                # Handle vehicle acquisition
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

                    print(f"\n✅ ORDER CREATED: {order_id}")
                    print(f"📧 Sending order confirmation email...")

                    # Send email
                    from database import orders_col

                    db_order = orders_col.find_one({"order_id": order_id})
                    if db_order:
                        enhanced_email_service.send_order_confirmation(db_order)
                        print(f"✅ Order confirmation email sent")

            elif session_state.active_agent == "phase2_service_manager":
                # Handle vehicle service/maintenance
                print(f"\n🔧 Routing to Phase 2 Service Manager...")
                result_state = run_async(phase2_service_manager.call(state))
                ai_reply = result_state["messages"][-1].content

                # Update session with Phase 2 context
                returned_context = result_state.get("context", {})

                appointment_created_flag = returned_context.get(
                    "appointment_created", False
                )

                # Store Phase 2 specific data in metadata
                metadata = session_state.metadata.copy()
                metadata.update(
                    {
                        "service_stage": returned_context.get("service_stage"),
                        "vehicle_info": returned_context.get("vehicle_info", {}),
                        "service_request": returned_context.get("service_request", {}),
                        "customer_service_info": returned_context.get(
                            "customer_service_info", {}
                        ),
                        "selected_provider": returned_context.get("selected_provider"),
                        "appointment_date": returned_context.get("appointment_date"),
                        "appointment_created": appointment_created_flag,
                        "appointment_id": returned_context.get("appointment_id"),
                    }
                )

                session_manager.update_session(
                    session_id,
                    {
                        "stage": returned_context.get(
                            "service_stage", session_state.stage
                        ),
                        "metadata": metadata,
                    },
                )

                if appointment_created_flag:
                    appointment_id = returned_context.get("appointment_id")
                    appointment_created = True

                    print(f"\n✅ APPOINTMENT CREATED: {appointment_id}")

                    # Verify appointment is in Services collection
                    if db is not None:
                        services_collection = db["Services"]
                        db_appointment = services_collection.find_one(
                            {"appointment_id": appointment_id}
                        )
                        if db_appointment:
                            print(f"✅ Appointment verified in Services collection")
                        else:
                            print(f"⚠️ Appointment not found in Services collection")

            else:
                ai_reply = "Agent in development"
        else:
            # Use supervisor to route
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
            metadata={
                "order_created": order_created,
                "order_id": order_id,
                "appointment_created": appointment_created,
                "appointment_id": appointment_id,
            },
        )

        response_data = {
            "reply": ai_reply,
            "success": True,
            "session_id": session_id,
            "order_created": order_created,
            "appointment_created": appointment_created,
        }

        if appointment_created:
            response_data["appointment_id"] = appointment_id
            response_data["session_ended"] = True

            # Add restart message to UI
            response_data[
                "reply"
            ] += "\n\n✅ **Appointment Booked & Confirmed!**\n\n💬 Type 'restart' or refresh to start a new conversation."

            # End session to clear all data
            print(f"\n🎉 APPOINTMENT BOOKING COMPLETE")
            print("=" * 70)
            print(f"📋 Appointment ID: {appointment_id}")
            print(
                f"👤 Customer Email: {session_state.metadata.get('customer_service_info', {}).get('email', 'N/A')}"
            )
            print(
                f"🚗 Vehicle: {session_state.metadata.get('vehicle_info', {}).get('make', 'N/A')} {session_state.metadata.get('vehicle_info', {}).get('model', 'N/A')}"
            )
            print(f"🧹 Clearing session: {session_id}")
            print("=" * 70)

            session_manager.end_session(session_id)
            print(f"✅ Session cleared and marked as ended")
            print(f"✅ Session ID {session_id} ready for fresh conversation\n")

        # Handle order completion - CLEAR SESSION
        if order_created:
            response_data["order_id"] = order_id
            response_data["session_ended"] = True

            # Add restart message
            response_data[
                "reply"
            ] += "\n\n✅ **Order Complete!**\n\n💬 Type 'restart' or refresh to start a new conversation."

            # End session after a delay
            print(f"🎉 Order completed - Clearing session: {session_id}")
            session_manager.end_session(session_id)

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
        from database import orders_col

        orders = list(orders_col.find().sort("created_at", -1).limit(50))
        for order in orders:
            order["_id"] = str(order["_id"])
            if isinstance(order.get("created_at"), datetime):
                order["created_at"] = order["created_at"].isoformat()
        return jsonify({"success": True, "orders": orders})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/appointments", methods=["GET"])
def get_all_appointments():
    """Get service appointments"""
    try:
        from service_appointment_manager import service_appointment_manager

        # Get from database
        if db is not None:
            appointments = list(
                db["service_appointments"].find().sort("created_at", -1).limit(50)
            )
            for apt in appointments:
                apt["_id"] = str(apt["_id"])
                if isinstance(apt.get("created_at"), datetime):
                    apt["created_at"] = apt["created_at"].isoformat()
                if isinstance(apt.get("updated_at"), datetime):
                    apt["updated_at"] = apt["updated_at"].isoformat()
            return jsonify({"success": True, "appointments": appointments})
        else:
            return jsonify({"success": True, "appointments": []})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check"""
    try:
        if db is not None:
            db.command("ping")
            db_status = "connected"
            car_count = cars_collection.count_documents({})
            order_count = orders_collection.count_documents({})
            appointment_count = (
                db["service_appointments"].count_documents({}) if db is not None else 0
            )
        else:
            db_status = "disconnected"
            car_count = 0
            order_count = 0
            appointment_count = 0
    except:
        db_status = "error"
        car_count = 0
        order_count = 0
        appointment_count = 0

    return jsonify(
        {
            "status": "healthy",
            "service": "Raava Enhanced Platform",
            "database": {
                "status": db_status,
                "cars": car_count,
                "orders": order_count,
                "appointments": appointment_count,
            },
            "features": {
                "session_management": "âœ… Active",
                "email_service": f"âœ… Active ({enhanced_email_service.config.email_enabled})",
                "dynamic_prompts": "âœ… Active",
                "phase1_concierge": "âœ… Active (Vehicle Acquisition)",
                "phase2_service_manager": "âœ… Active (Maintenance & Service)",
                "phase3_consigner": "â¸ï¸ Coming Soon (Vehicle Selling)",
            },
        }
    )


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ðŸš— RAAVA ENHANCED PLATFORM")
    print("=" * 70)
    print("âœ… Phase 1: AI Concierge (Vehicle Acquisition)")
    print("âœ… Phase 2: AI Service Manager (Maintenance & Service)")
    print("â¸ï¸  Phase 3: AI Consigner (Vehicle Selling) - Coming Soon")
    print("=" * 70)
    print("âœ… Session Management with Memory")
    print("âœ… Enhanced Email Service")
    print("âœ… Dynamic Configuration")
    print("=" * 70 + "\n")

    session_manager.cleanup_expired_sessions()

    app.run(debug=True, host="0.0.0.0", port=5000)
