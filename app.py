from flask import Flask, render_template, request, jsonify, send_file
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
import base64
from langgraph.workflow import create_graph
from langchain_core.messages import HumanMessage, AIMessage
import asyncio

load_dotenv()
app = Flask(__name__)

# MongoDB setup
client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
db = client["Raava_Sales"]
collection = db["Cars"]

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv(
    "ELEVENLABS_VOICE_ID", "mCQMfsqGDT6IDkEKR20a"
)  # Default voice

# Initialize LangGraph
graph = create_graph()

# Initialize LangGraph
graph = create_graph()


def run_async(coro):
    """Safely run an async coroutine in a sync environment like Flask."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def get_car_context():
    """Get all cars from database for context"""
    doc = collection.find_one({})
    if not doc or "cars" not in doc:
        return []
    return doc["cars"]


def download_image(url):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat-page")
def chat_page():
    return render_template("chat.html")


@app.route("/api/cars", methods=["GET"])
def get_cars():
    """Get all cars with optional filtering"""
    try:
        doc = collection.find_one({})
        if not doc or "cars" not in doc:
            return jsonify({"success": False, "message": "No cars found"}), 404

        cars = doc["cars"]

        # Apply filters from query parameters
        search_query = request.args.get("search", "").lower()
        make_filter = request.args.get("make", "").lower()
        sort_by = request.args.get("sort", "name")

        # Filter by search query
        if search_query:
            cars = [
                car
                for car in cars
                if search_query
                in car.get("key_information", {}).get("title", "").lower()
                or search_query
                in car.get("key_information", {}).get("make", "").lower()
            ]

        # Filter by make
        if make_filter:
            cars = [
                car
                for car in cars
                if make_filter in car.get("key_information", {}).get("make", "").lower()
            ]

        # Sort cars
        if sort_by == "price":
            cars = sorted(
                cars,
                key=lambda x: int(
                    x.get("pricing", "").split("£")[1].split("\n")[0].replace(",", "")
                    if "£" in x.get("pricing", "")
                    else 999999
                ),
            )
        else:  # name
            cars = sorted(
                cars,
                key=lambda x: x.get("key_information", {}).get("title", "").lower(),
            )

        return jsonify({"success": True, "cars": cars, "total": len(cars)})

    except Exception as e:
        print(f"Error in get_cars: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/makes", methods=["GET"])
def get_makes():
    """Get all unique car makes"""
    try:
        doc = collection.find_one({})
        if not doc or "cars" not in doc:
            return jsonify({"success": False, "message": "No cars found"}), 404

        makes = set()
        for car in doc["cars"]:
            make = car.get("key_information", {}).get("make", "Unknown")
            makes.add(make)

        return jsonify({"success": True, "makes": sorted(list(makes))})

    except Exception as e:
        print(f"Error in get_makes: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/car/<int:car_id>", methods=["GET"])
def get_car_details(car_id):
    """Get details for a specific car by index"""
    try:
        doc = collection.find_one({})
        if not doc or "cars" not in doc:
            return jsonify({"success": False, "message": "No cars found"}), 404

        cars = doc["cars"]
        if car_id < 0 or car_id >= len(cars):
            return jsonify({"success": False, "message": "Car not found"}), 404

        car = cars[car_id]
        return jsonify({"success": True, "car": car})

    except Exception as e:
        print(f"Error in get_car_details: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat endpoint with LangGraph Multi-Agent system"""
    try:
        user_msg = request.json.get("message", "")

        # Prepare state for LangGraph
        initial_state = {"messages": [HumanMessage(content=user_msg)], "next_agent": ""}

        async def get_reply():
            result = await graph.ainvoke(initial_state)
            return result["messages"][-1].content

        ai_reply = run_async(get_reply())

        return jsonify({"reply": ai_reply, "success": True})

    except Exception as e:
        print(f"Chat error: {str(e)}")
        return (
            jsonify(
                {
                    "reply": f"I apologize, but I'm having trouble processing your request. Please try again. Error: {str(e)}",
                    "success": False,
                }
            ),
            500,
        )


@app.route("/chat/image", methods=["POST"])
def chat_with_image():
    """Handle image upload and analysis"""
    try:
        if "image" not in request.files:
            return jsonify({"reply": "No image was uploaded.", "success": False}), 400

        file = request.files["image"]
        question = request.form.get(
            "message", "What car is this? Provide details about the model."
        )

        # Open and prepare image
        img = Image.open(file.stream)

        # Get car context
        cars = get_car_context()
        cars_list = "\n".join([f"- {car['name']}" for car in cars])

        prompt = f"""You are Raava, an automotive expert. Analyze this car image and provide detailed information.

Available cars in our inventory:
{cars_list}

Customer question: {question}

Please provide:
1. Car identification (make, model, approximate year if visible)
2. Whether this car or similar model is in our inventory
3. Key features visible in the image
4. Any other relevant details

Be helpful and informative."""

        # Call Gemini with image
        response = model.generate_content([prompt, img])

        return jsonify({"reply": response.text, "success": True})

    except Exception as e:
        print(f"Image chat error: {str(e)}")
        return (
            jsonify(
                {
                    "reply": f"I couldn't analyze the image. Error: {str(e)}",
                    "success": False,
                }
            ),
            500,
        )


@app.route("/api/text-to-speech", methods=["POST"])
def text_to_speech():
    """Convert text to speech using ElevenLabs API"""
    try:
        data = request.json
        text = data.get("text", "")

        if not text:
            return jsonify({"success": False, "message": "No text provided"}), 400

        if not ELEVENLABS_API_KEY:
            return (
                jsonify(
                    {"success": False, "message": "ElevenLabs API key not configured"}
                ),
                500,
            )

        # ElevenLabs TTS API endpoint
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

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            # Convert audio to base64
            audio_base64 = base64.b64encode(response.content).decode("utf-8")
            return jsonify({"success": True, "audio": audio_base64})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"ElevenLabs API error: {response.status_code}",
                    }
                ),
                500,
            )

    except Exception as e:
        print(f"TTS error: {str(e)}")
        return (
            jsonify({"success": False, "message": f"Text-to-speech error: {str(e)}"}),
            500,
        )


@app.route("/api/speech-to-text", methods=["POST"])
def speech_to_text():
    """Convert speech to text using browser's built-in Web Speech API"""
    # Note: The actual STT is handled on the client side using Web Speech API
    # This endpoint is kept for potential future server-side processing
    return jsonify({"success": True, "message": "STT is handled client-side"})


if __name__ == "__main__":
    app.run(debug=True)
