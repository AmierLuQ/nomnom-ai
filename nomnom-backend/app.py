# =======================================================================
#  Imports
# =======================================================================
# Standard library imports
import os
import datetime

# Third-party imports
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy.orm import joinedload
import pandas as pd

# Local application imports
from recommender import get_recommendations

# =======================================================================
# App Initialization & Configuration
# =======================================================================
app = Flask(__name__)
CORS(app)

# --- Database Configuration ---
# Get the database URL from environment variables for production
db_url = os.environ.get('DATABASE_URL')
# Adjust the URL prefix for SQLAlchemy if it's a Render Postgres URL
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
# Use the production URL or fall back to a local SQLite database for development
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///nomnom.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- JWT Configuration ---
# The secret key is used to sign the JWTs for security
app.config['JWT_SECRET_KEY'] = 'super-secret-key' # In production, this should be a more complex secret stored as an environment variable

# =======================================================================
# Initialize Extensions
# =======================================================================
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# =======================================================================
# Database Models (SQLAlchemy ORM)
# =======================================================================
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
    id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.String(20), db.ForeignKey('restaurant.id'), nullable=False)
    recommendation_rank = db.Column(db.Integer, nullable=True)
    user_action = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    swipe_time_sec = db.Column(db.Integer, nullable=True)
    final_ordered = db.Column(db.Boolean, nullable=True)
    user_feedback = db.Column(db.Text, nullable=True)

# =======================================================================
# API Endpoints
# =======================================================================

# -----------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------

@app.route('/api/register', methods=['POST'])
def register():
    """Registers a new user."""
    data = request.get_json()
    username = data.get('username').lower(); name = data.get('fullName'); email = data.get('email').lower(); phone = data.get('phone'); dob_str = data.get('dob'); password = data.get('password')
    dob = None; age = None
    if dob_str:
        try:
            dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d").date(); today = datetime.date.today(); age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except ValueError: return jsonify({'message': 'Invalid date format'}), 400
    last_user = User.query.order_by(User.id.desc()).first()
    next_id = f"USR_{int(last_user.id.split('_')[1]) + 1:03}" if last_user else "USR_001"
    if User.query.filter(func.lower(User.username) == username).first(): return jsonify({'message': 'Username already exists'}), 409
    if User.query.filter(func.lower(User.email) == email).first(): return jsonify({'message': 'Email already exists'}), 409
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    default_location = "4.38284661761217, 100.97441771522674"; lat, lon = map(float, default_location.split(", "))
    new_user = User(id=next_id, username=username, name=name, email=email, phone=phone, dob=dob, age=age, gender="M", location=default_location, latitude=lat, longitude=lon, last_login=None, password=hashed_pw)
    try:
        db.session.add(new_user); db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback(); print(f"❌ Registration error: {e}")
        return jsonify({'message': 'Server error during registration'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Logs in a user and returns a JWT access token."""
    data = request.get_json()
    username = data.get('username').lower(); password = data.get('password')
    user = User.query.filter(func.lower(User.username) == username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({'access_token': access_token, 'username': user.username}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# -----------------------------------------------------------------------
# User & Profile Endpoints
# -----------------------------------------------------------------------

@app.route('/api/users', methods=['GET'])
def get_users():
    """Returns a list of all users (for administrative purposes)."""
    try:
        users = User.query.all()
        result = [{'id': u.id, 'username': u.username, 'name': u.name, 'email': u.email, 'phone': u.phone, 'age': u.age, 'gender': u.gender, 'location': u.location, 'latitude': u.latitude, 'longitude': u.longitude, 'dob': u.dob.isoformat() if u.dob else None, 'last_login': u.last_login.isoformat() if u.last_login else None, 'created_at': u.created_at.isoformat() if u.created_at else None } for u in users]
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error in /api/users: {e}")
        return jsonify({'message': 'Server error fetching users'}), 500

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def user_profile():
    """Fetches detailed profile information for the currently logged-in user."""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user: return jsonify({'message': 'User not found'}), 404
        user_info = {'username': user.username, 'email': user.email, 'name': user.name, 'age': user.age, 'phone': user.phone}
        meals = Meal.query.filter_by(user_id=user_id).all()
        reviews = Review.query.filter_by(user_id=user_id).all()
        total_meals = len(meals)
        avg_rating = (sum(r.rating for r in reviews) / len(reviews)) if reviews else 0.0
        favorite_cuisine = 'N/A'
        if meals:
            meal_restaurant_ids = [m.restaurant_id for m in meals]
            if meal_restaurant_ids:
                tags = db.session.query(Restaurant.tag_1, Restaurant.tag_2, Restaurant.tag_3).filter(Restaurant.id.in_(meal_restaurant_ids)).all()
                tag_counts = pd.Series([tag for row in tags for tag in row if tag]).value_counts()
                if not tag_counts.empty: favorite_cuisine = tag_counts.index[0]
        stats = {'total_meals': total_meals, 'average_rating': avg_rating, 'favorite_cuisine': favorite_cuisine}
        recent_meals_query = db.session.query(Meal, Restaurant.name, Review.rating).join(Restaurant, Meal.restaurant_id == Restaurant.id).outerjoin(Review, (Review.user_id == Meal.user_id) & (Review.restaurant_id == Meal.restaurant_id)).filter(Meal.user_id == user_id).order_by(Meal.date.desc()).limit(5).all()
        recent_meals = [{'meal_id': meal.id, 'restaurant_name': name, 'date': meal.date.isoformat(), 'rating': rating} for meal, name, rating in recent_meals_query]
        return jsonify({'user_info': user_info, 'stats': stats, 'recent_meals': recent_meals}), 200
    except Exception as e:
        print(f"❌ Error in /api/profile: {e}")
        return jsonify({'message': 'Server error fetching profile data'}), 500

@app.route('/api/profile/update', methods=['POST'])
@jwt_required()
def update_user_profile():
    """Updates the name and phone number for the currently logged-in user."""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user: return jsonify({'message': 'User not found'}), 404
        data = request.get_json()
        user.name = data.get('name', user.name)
        user.phone = data.get('phone', user.phone)
        db.session.commit()
        updated_user_info = {'username': user.username, 'email': user.email, 'name': user.name, 'age': user.age, 'phone': user.phone}
        return jsonify({'message': 'Profile updated successfully!', 'user': updated_user_info}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in /api/profile/update: {e}")
        return jsonify({'message': 'Server error updating profile'}), 500

# -----------------------------------------------------------------------
# Restaurant & Recommendation Endpoints
# -----------------------------------------------------------------------

@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    """Returns a list of all restaurants in the database."""
    try:
        restaurants = Restaurant.query.all()
        result = [{'id': r.id, 'name': r.name, 'tags': [r.tag_1, r.tag_2, r.tag_3], 'google_rating': r.google_rating, 'price_range': f"{r.price_min} - {r.price_max}", 'location': f"{r.latitude}, {r.longitude}", 'description': r.description} for r in restaurants]
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error in /api/restaurants: {e}")
        return jsonify({'message': 'Server error fetching restaurants'}), 500

@app.route('/api/recommend', methods=['POST'])
@jwt_required()
def recommend():
    """
    Returns a personalized list of restaurant recommendations for the user.
    Accepts a list of 'exclude_ids' in the JSON body to support infinite scroll.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json(); exclude_ids = data.get('exclude_ids', [])
        exclude_ids.append('RST_901') # Always exclude "Home Cooked"
        recommended_ids = get_recommendations(user_id, exclude_ids=exclude_ids)
        if not recommended_ids:
            return jsonify({'user_id': user_id, 'recommendations': []}), 200
        recommendations = Restaurant.query.filter(Restaurant.id.in_(recommended_ids)).all()
        recommendations_dict = {r.id: r for r in recommendations}
        ordered_recs = [recommendations_dict[rid] for rid in recommended_ids if rid in recommendations_dict]
        result = [{'id': r.id, 'name': r.name, 'tags': [t for t in [r.tag_1, r.tag_2, r.tag_3] if t], 'google_rating': r.google_rating, 'price_range': f"{r.price_min} - {r.price_max}", 'location': f"{r.latitude},{r.longitude}", 'description': r.description, 'address': r.address, 'opening_time': r.opening_time, 'closing_time': r.closing_time, 'phone': r.phone} for r in ordered_recs]
        return jsonify({'user_id': user_id, 'recommendations': result}), 200
    except Exception as e:
        print(f"❌ Error in /api/recommend: {e}")
        return jsonify({'message': 'Error generating recommendations'}), 500

# -----------------------------------------------------------------------
# Debugging Endpoints
# -----------------------------------------------------------------------

@app.route('/api/debug', methods=['GET'])
def debug_config():
    """A utility endpoint to check the live database configuration."""
    configured_db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    return jsonify({
        'message': 'This is the configuration the live app is using.',
        'SQLALCHEMY_DATABASE_URI': configured_db_url
    }), 200

# =======================================================================
# Main Execution
# =======================================================================
if __name__ == '__main__':
    # This block runs the app when the script is executed directly
    # (e.g., `python app.py`). The `debug=True` flag enables
    # auto-reloading and provides detailed error pages during development.
    app.run(debug=True)
