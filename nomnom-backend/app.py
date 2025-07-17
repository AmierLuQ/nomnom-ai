from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import func
from recommender import get_recommendations
import datetime
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# --- Configurations ---
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///nomnom.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key' # Consider changing this and storing it as an environment variable too

# --- Initialize Extensions ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.String(20), primary_key=True)
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

class Restaurant(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    district = db.Column(db.String(120), nullable=True)
    price_min = db.Column(db.String(20), nullable=True)
    price_max = db.Column(db.String(20), nullable=True)
    google_rating = db.Column(db.Float, nullable=True)
    num_google_reviews = db.Column(db.Integer, nullable=True)
    opening_time = db.Column(db.String(10), nullable=True)
    closing_time = db.Column(db.String(10), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    tag_1 = db.Column(db.String(50), nullable=True)
    tag_2 = db.Column(db.String(50), nullable=True)
    tag_3 = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)

class Meal(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'))
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurant.id'))
    date = db.Column(db.Date, nullable=False)
    day = db.Column(db.String(20), nullable=True)
    meal_time = db.Column(db.String(20), nullable=True)

class Review(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'))
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurant.id'))
    date = db.Column(db.Date, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    price_satisfaction = db.Column(db.Boolean, nullable=True)
    visit_frequency = db.Column(db.Integer, nullable=True)

class InteractionLog(db.Model):
    id = db.Column(db.String(20), primary_key=True)  # LOG_001_001_A
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurant.id'), nullable=False)
    recommendation_rank = db.Column(db.Integer, nullable=True)
    user_action = db.Column(db.String(50), nullable=False)  # decline, favorite, eat
    timestamp = db.Column(db.DateTime, nullable=False)
    swipe_time_sec = db.Column(db.Integer, nullable=True)
    final_ordered = db.Column(db.Boolean, nullable=True)
    user_feedback = db.Column(db.Text, nullable=True)

# Create tables if not exist
with app.app_context():
    db.create_all()

# --- API Endpoints ---

# ✅ Get Users
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        result = [{
            'id': u.id,
            'username': u.username,
            'name': u.name,
            'email': u.email,
            'phone': u.phone,
            'age': u.age,
            'gender': u.gender,
            'location': u.location,
            'latitude': u.latitude,
            'longitude': u.longitude,
            'dob': u.dob.isoformat() if u.dob else None,
            'last_login': u.last_login.isoformat() if u.last_login else None,
            'created_at': u.created_at.isoformat() if u.created_at else None
        } for u in users]
        return jsonify(result), 200
    except Exception as e:
        print("❌ Error in /api/users:", e)
        return jsonify({'message': 'Server error fetching users'}), 500

# ✅ Register
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username').lower()
    name = data.get('fullName')
    email = data.get('email').lower()
    phone = data.get('phone')
    dob_str = data.get('dob')
    password = data.get('password')

    dob = None
    age = None
    if dob_str:
        try:
            dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except ValueError:
            return jsonify({'message': 'Invalid date format'}), 400

    last_user = User.query.order_by(User.id.desc()).first()
    next_id = f"USR_{int(last_user.id.split('_')[1]) + 1:03}" if last_user else "USR_001"

    if User.query.filter(func.lower(User.username) == username).first():
        return jsonify({'message': 'Username already exists'}), 409
    if User.query.filter(func.lower(User.email) == email).first():
        return jsonify({'message': 'Email already exists'}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    default_location = "4.38284661761217, 100.97441771522674"
    lat, lon = map(float, default_location.split(", "))

    new_user = User(
        id=next_id,
        username=username,
        name=name,
        email=email,
        phone=phone,
        dob=dob,
        age=age,
        gender="M",
        location=default_location,
        latitude=lat,
        longitude=lon,
        last_login=None,
        password=hashed_pw
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        print("❌ Registration error:", e)
        return jsonify({'message': 'Server error during registration'}), 500

# ✅ Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username').lower()
    password = data.get('password')

    user = User.query.filter(func.lower(User.username) == username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({'access_token': access_token, 'username': user.username}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# ✅ Get All Restaurants
@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    try:
        restaurants = Restaurant.query.all()
        result = [{
            'id': r.id,
            'name': r.name,
            'tags': [r.tag_1, r.tag_2, r.tag_3],
            'google_rating': r.google_rating,
            'price_range': f"{r.price_min} - {r.price_max}",
            'location': f"{r.latitude}, {r.longitude}",
            'description': r.description
        } for r in restaurants]
        return jsonify(result), 200
    except Exception as e:
        print("❌ Error in /api/restaurants:", e)
        return jsonify({'message': 'Server error fetching restaurants'}), 500

# ✅ Recommend Restaurants 
@app.route('/api/recommend', methods=['GET'])
@jwt_required()
def recommend():
    try:
        user_id = get_jwt_identity()
        
        # Call our new recommendation function
        recommended_ids = get_recommendations(user_id)
        
        if not recommended_ids:
            # Fallback: if no recommendations, return top rated globally
            recommended_ids = [r.id for r in Restaurant.query.order_by(Restaurant.google_rating.desc()).limit(10).all()]

        # Fetch full restaurant details from the database based on IDs
        # The 'in_' operator requires a list of values
        recommendations = Restaurant.query.filter(Restaurant.id.in_(recommended_ids)).all()
        
        # Preserve the order from the recommendation engine
        recommendations_dict = {r.id: r for r in recommendations}
        ordered_recs = [recommendations_dict[rid] for rid in recommended_ids if rid in recommendations_dict]

        result = [{
            'id': r.id,
            'name': r.name,
            'tags': [tag for tag in [r.tag_1, r.tag_2, r.tag_3] if tag], # Clean up null tags
            'google_rating': r.google_rating,
            'price_range': f"{r.price_min} - {r.price_max}",
            'location': f"{r.latitude},{r.longitude}",
            'description': r.description,
            'address': r.address,
            'opening_time': r.opening_time,
            'closing_time': r.closing_time,
            'phone': r.phone
        } for r in ordered_recs]
        
        return jsonify({'user_id': user_id, 'recommendations': result}), 200

    except Exception as e:
        print(f"❌ Error in /api/recommend: {e}")
        return jsonify({'message': 'Error generating recommendations'}), 500

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)