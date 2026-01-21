"""
Raava Enhanced App - FIXED AUTO-GREETING & SMART ROUTING
- Auto-greets users on first load
- Routes based on query intent (no asking buy/service/sell)
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
    orders_collection,
    conversations_collection,
)

# Use Scraped_Cars collection
from database import db as database_instance

scraped_cars_collection = (
    database_instance["Scraped_Cars"] if database_instance is not None else None
)


# Import agents - ALL 3 PHASES
from supervisor_agent import supervisor_agent
from phase1_concierge import phase1_concierge
from phase2_service_manager import phase2_service_manager
from phase3_consigner import phase3_consigner

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


@app.route("/listings")
def listings_page():
    """View all consignment listings"""
    return render_template("listings.html")


@app.route("/api/cars", methods=["GET"])
def get_cars():
    """Get cars from Scraped_Cars collection"""
    try:
        make = request.args.get("make", "")
        query = {}
        if make:
            query["make"] = {"$regex": make, "$options": "i"}

        cars = list(scraped_cars_collection.find(query).limit(50))

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


@app.route("/api/consignments", methods=["GET"])
def get_consignments():
    """Get all consignment listings from Consignments collection"""
    try:
        if db is None:
            return jsonify({"success": True, "listings": []})

        consignments_col = db["Consignments"]

        # Get query parameters
        status = request.args.get("status", "")
        make = request.args.get("make", "")

        query = {}
        if status:
            query["status"] = status
        if make:
            query["vehicle.make"] = {"$regex": make, "$options": "i"}

        listings = list(consignments_col.find(query).sort("created_at", -1).limit(100))

        # Format listings
        formatted_listings = []
        for listing in listings:
            formatted_listings.append(
                {
                    "_id": str(listing["_id"]),
                    "listing_id": listing.get("listing_id"),
                    "status": listing.get("status"),
                    "vehicle": listing.get("vehicle", {}),
                    "pricing": listing.get("pricing", {}),
                    "specifications": listing.get("specifications", {}),
                    "condition": listing.get("condition", {}),
                    "listing": listing.get("listing", {}),
                    "marketplaces": listing.get("marketplaces", []),
                    "owner": listing.get("owner", {}),
                    "created_at": (
                        listing.get("created_at").isoformat()
                        if isinstance(listing.get("created_at"), datetime)
                        else None
                    ),
                    "views": listing.get("views", 0),
                    "inquiries": listing.get("inquiries", 0),
                }
            )

        return jsonify({"success": True, "listings": formatted_listings})
    except Exception as e:
        print(f"❌ Error fetching consignments: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/listing/<listing_id>", methods=["GET"])
def get_listing(listing_id):
    """Get a specific listing by ID"""
    try:
        if db is None:
            return jsonify({"success": False, "message": "Database not connected"}), 500

        consignments_col = db["Consignments"]
        listing = consignments_col.find_one({"listing_id": listing_id})

        if not listing:
            return jsonify({"success": False, "message": "Listing not found"}), 404

        # Format listing for display
        formatted = {
            "_id": str(listing["_id"]),
            "listing_id": listing.get("listing_id"),
            "status": listing.get("status"),
            "vehicle": listing.get("vehicle", {}),
            "pricing": listing.get("pricing", {}),
            "condition": listing.get("condition", {}),
            "owner": listing.get("owner", {}),
            "created_at": (
                listing.get("created_at").isoformat()
                if isinstance(listing.get("created_at"), datetime)
                else None
            ),
        }

        return jsonify({"success": True, "listing": formatted})

    except Exception as e:
        print(f"❌ Error fetching listing: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat with FIXED AUTO-GREETING & SMART ROUTING"""
    try:
        data = request.json
        user_msg = data.get("message", "")
        session_id = (
            data.get("session_id")
            or flask_session.get("session_id")
            or str(uuid.uuid4())
        )

        # 🔥 FIXED: Auto-greet on empty message (first load)
        if not user_msg.strip():
            flask_session["session_id"] = session_id
            return jsonify(
                {
                    "reply": "Welcome to Raava! How can I help you today? 😊",
                    "success": True,
                    "session_id": session_id,
                }
            )

        # Store session_id in flask session
        flask_session["session_id"] = session_id

        # Get or create session
        session_state = session_manager.get_session(session_id)

        print(f"\n📋 Session: {session_id}")
        print(f"📊 Stage: {session_state.stage}")
        print(f"🤖 Active Agent: {session_state.active_agent}")
        print(f"🎯 Routed: {session_state.routed}")

        # Prepare messages
        messages = []
        for turn in session_state.conversation_history[-5:]:
            messages.append(HumanMessage(content=turn["user_message"]))
            messages.append(AIMessage(content=turn["ai_response"]))
        messages.append(HumanMessage(content=user_msg))

        # Prepare state with all phase contexts
        state = {
            "messages": messages,
            "context": {
                "session_id": session_id,
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
                # Phase 2 context
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
                # Phase 3 context
                "consigner_stage": session_state.metadata.get("consigner_stage"),
                "vehicle_details": session_state.metadata.get("vehicle_details", {}),
                "service_history": session_state.metadata.get("service_history", {}),
                "specifications": session_state.metadata.get("specifications", {}),
                "condition": session_state.metadata.get("condition", {}),
                "photos_ready": session_state.metadata.get("photos_ready", False),
                "valuation": session_state.metadata.get("valuation", {}),
                "asking_price": session_state.metadata.get("asking_price", 0),
                "marketplaces": session_state.metadata.get("marketplaces", []),
                "owner_details": session_state.metadata.get("owner_details", {}),
                "listing_created": session_state.metadata.get("listing_created", False),
                "listing_id": session_state.metadata.get("listing_id"),
            },
            "session_id": session_id,
        }

        ai_reply = ""
        order_created = False
        order_id = None
        appointment_created = False
        appointment_id = None
        listing_created = False
        listing_id = None

        # 🔥 ROUTING LOGIC
        if session_state.routed and session_state.active_agent:
            print(f"🎯 Routing to: {session_state.active_agent}")

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
                    print(f"✅ ORDER CREATED: {order_id}")

            elif session_state.active_agent == "phase2_service_manager":
                # Handle vehicle service/maintenance
                result_state = run_async(phase2_service_manager.call(state))
                ai_reply = result_state["messages"][-1].content

                # Update session with Phase 2 context
                returned_context = result_state.get("context", {})
                appointment_created_flag = returned_context.get(
                    "appointment_created", False
                )

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
                    print(f"✅ APPOINTMENT CREATED: {appointment_id}")

            elif session_state.active_agent == "phase3_consigner":
                # Handle vehicle consignment
                result_state = run_async(phase3_consigner.call(state))
                ai_reply = result_state["messages"][-1].content

                # Update session with Phase 3 context
                returned_context = result_state.get("context", {})
                listing_created_flag = returned_context.get("listing_created", False)

                metadata = session_state.metadata.copy()
                metadata.update(
                    {
                        "consigner_stage": returned_context.get("consigner_stage"),
                        "vehicle_details": returned_context.get("vehicle_details", {}),
                        "service_history": returned_context.get("service_history", {}),
                        "specifications": returned_context.get("specifications", {}),
                        "condition": returned_context.get("condition", {}),
                        "photos_ready": returned_context.get("photos_ready", False),
                        "valuation": returned_context.get("valuation", {}),
                        "asking_price": returned_context.get("asking_price", 0),
                        "marketplaces": returned_context.get("marketplaces", []),
                        "owner_details": returned_context.get("owner_details", {}),
                        "listing_created": listing_created_flag,
                        "listing_id": returned_context.get("listing_id"),
                    }
                )

                session_manager.update_session(
                    session_id,
                    {
                        "stage": returned_context.get(
                            "consigner_stage", session_state.stage
                        ),
                        "metadata": metadata,
                    },
                )

                if listing_created_flag:
                    listing_id = returned_context.get("listing_id")
                    listing_created = True
                    print(f"✅ LISTING CREATED: {listing_id}")

            else:
                # Unknown agent - revert to supervisor
                print(
                    f"⚠️ Unknown agent: {session_state.active_agent} - reverting to supervisor"
                )

                session_manager.update_session(
                    session_id,
                    {
                        "routed": False,
                        "active_agent": None,
                    },
                )

                result_state = run_async(supervisor_agent.call(state))
                ai_reply = result_state["messages"][-1].content

                if result_state.get("route_to"):
                    print(f"🎯 Supervisor re-routing to: {result_state['route_to']}")
                    session_manager.update_session(
                        session_id,
                        {
                            "routed": True,
                            "active_agent": result_state["route_to"],
                        },
                    )
        else:
            # 🔥 Use supervisor for SMART ROUTING (no asking)
            print("🎯 Using supervisor for smart routing...")
            result_state = run_async(supervisor_agent.call(state))
            ai_reply = result_state["messages"][-1].content

            if result_state.get("route_to"):
                print(f"🎯 Supervisor routing to: {result_state['route_to']}")
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
                "listing_created": listing_created,
                "listing_id": listing_id,
            },
        )

        response_data = {
            "reply": ai_reply,
            "success": True,
            "session_id": session_id,
            "order_created": order_created,
            "appointment_created": appointment_created,
            "listing_created": listing_created,
        }

        # Handle completion and session clearing
        if appointment_created or order_created or listing_created:
            response_data["session_ended"] = True

            completion_type = (
                "Order"
                if order_created
                else ("Appointment" if appointment_created else "Listing")
            )
            completion_id = order_id or appointment_id or listing_id

            response_data[
                "reply"
            ] += f"\n\n✅ **{completion_type} Complete!**\n\n💬 Type 'restart' or refresh to start a new conversation."

            print(f"🎉 {completion_type.upper()} COMPLETE: {completion_id}")
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
        if db is not None:
            appointments = list(db["Services"].find().sort("created_at", -1).limit(50))
            for apt in appointments:
                apt["_id"] = str(apt["_id"])
                if isinstance(apt.get("created_at"), datetime):
                    apt["created_at"] = apt["created_at"].isoformat()
            return jsonify({"success": True, "appointments": appointments})
        else:
            return jsonify({"success": True, "appointments": []})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check - simplified for render"""
    try:
        db_status = "unknown"
        car_count = order_count = appointment_count = listing_count = 0

        if db is not None:
            try:
                db.command("ping")
                db_status = "connected"

                if scraped_cars_collection:
                    car_count = scraped_cars_collection.count_documents({})
                if orders_collection:
                    order_count = orders_collection.count_documents({})
                if db["Services"]:
                    appointment_count = db["Services"].count_documents({})
                if db["Consignments"]:
                    listing_count = db["Consignments"].count_documents({})
            except Exception as e:
                print(f"DB query error: {e}")
                db_status = "connected_limited"
        else:
            db_status = "disconnected"
    except Exception as e:
        print(f"Health check error: {e}")
        db_status = "error"

    return jsonify(
        {
            "status": "healthy",
            "service": "Raava Complete Platform",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": db_status,
                "cars": car_count,
                "orders": order_count,
                "appointments": appointment_count,
                "listings": listing_count,
            },
            "features": {
                "session_management": "Active",
                "email_service": "Active",
                "phase1_concierge": "Active (Vehicle Acquisition)",
                "phase2_service_manager": "Active (Maintenance & Service)",
                "phase3_consigner": "Active (Vehicle Consignment)",
            },
        }
    )


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚗 RAAVA COMPLETE PLATFORM - ALL 3 PHASES")
    print("=" * 70)
    print("✅ Phase 1: AI Concierge (Vehicle Acquisition)")
    print("✅ Phase 2: AI Service Manager (Maintenance & Service)")
    print("✅ Phase 3: AI Consigner (Vehicle Consignment)")
    print("=" * 70 + "\n")

    session_manager.cleanup_expired_sessions()
    app.run(debug=True, host="0.0.0.0", port=5000)
