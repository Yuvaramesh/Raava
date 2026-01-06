from flask import Flask, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

app = Flask(__name__)

# MongoDB connection
client = MongoClient(os.getenv("MONGO_CONNECTION_STRING"))
db = client["raava_multiagent"]  # your database name
collection = db["cardata"]  # your collection name


@app.route("/")
def home():
    document = collection.find_one({"_id": ObjectId("695bbc1f36619f5988739fcd")})

    cars = document["data"]
    return render_template("index.html", cars=cars)


if __name__ == "__main__":
    app.run(debug=True)
