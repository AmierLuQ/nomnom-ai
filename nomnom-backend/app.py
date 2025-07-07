from flask import Flask, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Load pre-converted JSON
with open("restaurants.json", "r", encoding="utf-8") as f:
    restaurants = json.load(f)

@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    return jsonify(restaurants)

if __name__ == "__main__":
    app.run(debug=True)
