from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
import json
import os

with open('data/users.json', 'r', encoding='utf-8') as f:
    user_json_data = json.load(f)

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

# --- User Model ---
class User(db.Model):
    id = db.Column(db.String(20), primary_key=True)  # USR_001 etc.
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# Create tables if they don’t exist
with app.app_context():
    db.create_all()

# --- API Endpoints ---

# ✅ Check User List
@app.route('/api/users', methods=['GET'])
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    result = []

    for user in users:
        # Basic DB info
        user_data = {
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'dob' : user.dob
        }

        # Find matching JSON entry by username
        json_entry = next((u for u in user_json_data if u["Username"].lower() == user.username), None)
        if json_entry:
            # Merge extra fields
            user_data.update({
                'age': json_entry.get('Age'),
                'gender': json_entry.get('Gender'),
                'location': json_entry.get('Location'),
                'last_login': json_entry.get('Last Login'),
                'latitude': json_entry.get('Latitude'),
                'longitude': json_entry.get('Longitude'),
            })

        result.append(user_data)

    return jsonify(result), 200



# ✅ Register User
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username').lower()
    name = data.get('fullName')  # ✅ React sends fullName
    email = data.get('email')
    phone = data.get('phone')
    dob_str = data.get('dob')    # Expecting YYYY-MM-DD
    password = data.get('password')

    # Handle DOB safely
    dob = None
    if dob_str:
        try:
            dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({'message': 'Invalid date format'}), 400

    # Check for duplicate username or email
    if User.query.filter(db.func.lower(User.username) == username).first():
        return jsonify({'message': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(
        username=username,
        name=name,
        email=email,
        phone=phone,
        dob=dob,
        password=hashed_pw
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        print("Registration error:", e)
        return jsonify({'message': 'Server error during registration'}), 500



# ✅ Login User
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username').lower()  # ✅ Username here
    password = data.get('password')

    user = User.query.filter(db.func.lower(User.username) == username).first()
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
