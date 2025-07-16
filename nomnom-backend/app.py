from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
import json
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# --- Configurations ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nomnom.db'  # SQLite for development
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # Change this for production

# --- Initialize Extensions ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# --- Load JSON Data ---
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')

def load_json(filename):
    filepath = os.path.join(DATA_FOLDER, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

restaurants = load_json('restaurants.json')
tags = load_json('tags.json')
meal_times = load_json('meal_times.json')

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)  # 👈 Full name
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)   # 👈 Phone number
    dob = db.Column(db.Date, nullable=True)           # 👈 Date of birth
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Create tables if they don’t exist
with app.app_context():
    db.create_all()

# --- API Endpoints ---

# ✅ Register User
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    name = data.get('fullName')  # 👈 Get full name
    email = data.get('email')
    phone = data.get('phone')    # 👈 Get phone
    dob_str = data.get('dob')    # 👈 Get dob as string (e.g., "2025-07-16")
    password = data.get('password')

    # Parse DOB string to date object
    dob = None
    if dob_str:
        dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d").date()

    # Check if user exists
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already registered'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 409

    # Hash password
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create new user
    new_user = User(
        username=username,
        name=name,
        email=email,
        phone=phone,
        dob=dob,
        password=hashed_pw
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


# ✅ Login User
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')  # <-- Use username
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': access_token,
            'username': user.username
        }), 200
    return jsonify({'message': 'Invalid credentials'}), 401


# ✅ Get All Restaurants
@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    return jsonify(restaurants), 200

# ✅ Recommend Restaurants (mock: top 5)
@app.route('/api/recommend', methods=['GET'])
@jwt_required()
def recommend():
    user_id = int(get_jwt_identity())  # Get logged-in user ID
    recommendations = restaurants[:5]  # Mock: Top 5 restaurants
    return jsonify({'user_id': user_id, 'recommendations': recommendations}), 200

# ✅ Get Tags
@app.route('/api/tags', methods=['GET'])
def get_tags():
    return jsonify(tags), 200

# ✅ Get Meal Times
@app.route('/api/mealtimes', methods=['GET'])
def get_mealtimes():
    return jsonify(meal_times), 200

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)
