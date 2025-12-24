from flask import Flask, render_template, request, jsonify, send_file
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
import base64

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
            cars = [car for car in cars if search_query in car["name"].lower()]

        # Filter by make
        if make_filter:
            cars = [car for car in cars if make_filter in car["name"].lower()]

        # Sort cars
        if sort_by == "name":
            cars = sorted(cars, key=lambda x: x["name"])

        return jsonify({"success": True, "cars": cars, "total": len(cars)})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/car/<car_name>", methods=["GET"])
def get_car_details(car_name):
    """Get details for a specific car"""
    try:
        doc = collection.find_one({})
        if not doc:
            return jsonify({"success": False, "message": "No cars found"}), 404

        car = next(
            (c for c in doc["cars"] if c["name"].lower() == car_name.lower()), None
        )

        if car:
            return jsonify({"success": True, "car": car})
        else:
            return jsonify({"success": False, "message": "Car not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/makes", methods=["GET"])
def get_makes():
    """Get all unique car makes"""
    try:
        doc = collection.find_one({})
        if not doc:
            return jsonify({"success": False, "message": "No cars found"}), 404

        makes = set()
        for car in doc["cars"]:
            make = car["name"].split()[0]
            makes.add(make)

        return jsonify({"success": True, "makes": sorted(list(makes))})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat endpoint with Gemini AI"""
    try:
        user_msg = request.json.get("message", "")
        car_name = request.json.get(
            "carName", ""
        )  # Optional: if user is viewing a specific car

        # Get all cars for context
        cars = get_car_context()
        if not cars:
            return jsonify(
                {
                    "reply": "Sorry, I couldn't access the car database.",
                    "success": False,
                }
            )

        # Find the specific car if mentioned
        current_car = None
        car_images = []

        # Check if car_name is provided or find it in the message
        if car_name:
            current_car = next(
                (c for c in cars if c["name"].lower() == car_name.lower()), None
            )
        else:
            # Try to find car mentioned in message
            for car in cars:
                if car["name"].lower() in user_msg.lower():
                    current_car = car
                    break

        # Prepare context for Gemini
        cars_list = "\n".join([f"- {car['name']}" for car in cars])

        system_context = f"""You are Raava, a premium automotive sales consultant specializing in luxury and high-performance vehicles for the UK market.

Available vehicles in our exclusive collection:
{cars_list}

Your expertise includes:
1. Detailed knowledge of luxury car specifications, performance features, and cutting-edge technology
2. UK market pricing (OTR - On The Road prices including VAT, first registration fee, number plates, and road tax)
3. Comparative analysis of premium and luxury models
4. Performance metrics, fuel economy (mpg), CO2 emissions, and WLTP figures
5. Safety ratings (Euro NCAP), driver assistance systems, and premium features
6. Finance options including PCP (Personal Contract Purchase), HP (Hire Purchase), and leasing

UK Market Guidelines:
- All prices should be in GBP (£) with realistic UK market estimates
- OTR (On The Road) price includes: List price + First registration fee + Number plates + 12 months road tax + Delivery charges
- Discuss road tax bands based on CO2 emissions (relevant for UK)
- Mention fuel economy in mpg (miles per gallon) and CO2 emissions in g/km
- Reference ULEZ (Ultra Low Emission Zone) compliance for London buyers when relevant
- Discuss insurance groups (1-50 scale in UK)
- Be aware of company car tax implications and BIK (Benefit in Kind) rates for business buyers

Tone & Approach:
- Sophisticated yet approachable - we're selling premium vehicles to discerning clients
- Emphasize British motoring heritage, German engineering excellence, or Italian craftsmanship as appropriate
- Focus on the ownership experience, not just the transaction
- Highlight exclusive features, bespoke options, and premium materials
- Keep responses professional, refined, and informative
- Use British English spelling and terminology

Current conversation context:
"""

        if current_car:
            system_context += (
                f"\nThe customer is currently viewing: {current_car['name']}"
            )
            images_data = current_car.get("image", [])
            if isinstance(images_data, str):
                car_images = [images_data]
            else:
                car_images = images_data

        # Prepare content for Gemini
        prompt_parts = [system_context, f"\nCustomer question: {user_msg}"]

        # If we have images and the query might benefit from visual context
        if car_images and len(car_images) > 0:
            # Download first image for vision analysis
            img = download_image(car_images[0])
            if img:
                prompt_parts.insert(1, img)

        # Call Gemini API
        response = model.generate_content(prompt_parts)
        ai_reply = response.text

        # Return response with images if specific car was found
        result = {"reply": ai_reply, "success": True}

        if current_car:
            result["car"] = current_car
            result["image"] = car_images[:4]  # Limit to 4 images

        return jsonify(result)

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
