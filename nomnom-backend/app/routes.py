# =======================================================================
# app/routes.py
# -----------------------------------------------------------------------
# This file contains all the API endpoints (routes) for the application,
# organized using a Flask Blueprint.
# =======================================================================

# Standard library imports
import datetime
import pandas as pd
from zoneinfo import ZoneInfo

# Third-party imports
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import func

# Local application imports
from app import db, bcrypt
from app.models import User, Restaurant, Meal, Review, InteractionLog
from recommender import get_recommendations

# Create a Blueprint object. All routes will be registered with this blueprint.
main = Blueprint('main', __name__)

# =======================================================================
# API Endpoints
# =======================================================================

# -----------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------

@main.route('/api/register', methods=['POST'])
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

@main.route('/api/login', methods=['POST'])
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

@main.route('/api/users', methods=['GET'])
def get_users():
    """Returns a list of all users (for administrative purposes)."""
    try:
        users = User.query.all()
        result = [{'id': u.id, 'username': u.username, 'name': u.name, 'email': u.email, 'phone': u.phone, 'age': u.age, 'gender': u.gender, 'location': u.location, 'latitude': u.latitude, 'longitude': u.longitude, 'dob': u.dob.isoformat() if u.dob else None, 'last_login': u.last_login.isoformat() if u.last_login else None, 'created_at': u.created_at.isoformat() if u.created_at else None } for u in users]
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error in /api/users: {e}")
        return jsonify({'message': 'Server error fetching users'}), 500

@main.route('/api/profile', methods=['GET'])
@jwt_required()
def user_profile():
    """Fetches detailed profile information for the currently logged-in user."""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user: return jsonify({'message': 'User not found'}), 404
        user_info = {'username': user.username, 'email': user.email, 'name': user.name, 'age': user.age, 'phone': user.phone, 'gender': user.gender, 'location': user.location}
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
        
        recent_meals_query = db.session.query(Meal, Restaurant.name).join(Restaurant, Meal.restaurant_id == Restaurant.id).filter(Meal.user_id == user_id).order_by(Meal.date.desc()).limit(5).all()
        recent_meals = []
        for meal, name in recent_meals_query:
            latest_review = Review.query.filter_by(user_id=user_id, restaurant_id=meal.restaurant_id).order_by(Review.date.desc()).first()
            recent_meals.append({
                'meal_id': meal.id, 'restaurant_name': name, 'date': meal.date.isoformat(), 
                'meal_time': meal.meal_time, 
                'rating': latest_review.rating if latest_review else None
            })
            
        return jsonify({'user_info': user_info, 'stats': stats, 'recent_meals': recent_meals}), 200
    except Exception as e:
        print(f"❌ Error in /api/profile: {e}")
        return jsonify({'message': 'Server error fetching profile data'}), 500

@main.route('/api/profile/update', methods=['POST'])
@jwt_required()
def update_user_profile():
    """Updates profile information for the currently logged-in user."""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user: return jsonify({'message': 'User not found'}), 404
        data = request.get_json()
        user.name = data.get('name', user.name)
        user.phone = data.get('phone', user.phone)
        user.gender = data.get('gender', user.gender)
        user.location = data.get('location', user.location)
        db.session.commit()
        updated_user_info = {'username': user.username, 'email': user.email, 'name': user.name, 'age': user.age, 'phone': user.phone, 'gender': user.gender, 'location': user.location}
        return jsonify({'message': 'Profile updated successfully!', 'user': updated_user_info}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in /api/profile/update: {e}")
        return jsonify({'message': 'Server error updating profile'}), 500

@main.route('/api/profile/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Changes the password for the currently logged-in user."""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user: return jsonify({'message': 'User not found'}), 404

        data = request.get_json()
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')

        if not bcrypt.check_password_hash(user.password, current_password):
            return jsonify({'message': 'Current password is incorrect'}), 401

        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        return jsonify({'message': 'Password updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in /api/profile/change-password: {e}")
        return jsonify({'message': 'Server error changing password'}), 500

# -----------------------------------------------------------------------
# Restaurant & Recommendation Endpoints
# -----------------------------------------------------------------------

@main.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    """Returns a list of all restaurants in the database."""
    try:
        restaurants = Restaurant.query.all()
        result = [{'id': r.id, 'name': r.name, 'tags': [r.tag_1, r.tag_2, r.tag_3], 'google_rating': r.google_rating, 'price_range': f"{r.price_min} - {r.price_max}", 'location': f"{r.latitude}, {r.longitude}", 'description': r.description} for r in restaurants]
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ Error in /api/restaurants: {e}")
        return jsonify({'message': 'Server error fetching restaurants'}), 500

@main.route('/api/recommend', methods=['POST'])
@jwt_required()
def recommend():
    """Returns a personalized list of restaurant recommendations for the user."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json(); exclude_ids = data.get('exclude_ids', [])
        exclude_ids.append('RST_901')
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

# --- MODIFIED: Endpoint to handle user ratings and meals ---
@main.route('/api/rate', methods=['POST'])
@jwt_required()
def rate_restaurant():
    """Creates a meal entry and creates/updates a user's review for a restaurant."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        restaurant_id = data.get('restaurant_id')
        rating = data.get('rating')

        if not all([restaurant_id, rating]):
            return jsonify({'message': 'Missing restaurant_id or rating'}), 400

        
        malaysia_tz = ZoneInfo("Asia/Kuala_Lumpur")
        now = datetime.datetime.now(malaysia_tz)
        day = now.strftime('%A')
        hour = now.hour + now.minute / 60.0
        
        if 4.0 <= hour < 7.0: meal_time = "Suhoor"
        elif 7.0 <= hour < 10.0: meal_time = "Breakfast"
        elif 10.0 <= hour < 12.0: meal_time = "Brunch"
        elif 12.0 <= hour < 16.0: meal_time = "Lunch"
        elif 16.0 <= hour < 17.5: meal_time = "Tea Time"
        elif 17.5 <= hour < 19.5: meal_time = "Linner"
        elif 19.5 <= hour < 22.0: meal_time = "Dinner"
        elif 22.0 <= hour < 23.5: meal_time = "Late Dinner"
        else: meal_time = "Midnight Snack"

        # Generate a new unique Meal ID
        last_meal = Meal.query.filter_by(user_id=user_id).order_by(Meal.id.desc()).first()
        meal_count = int(last_meal.id.split('_')[-1]) + 1 if last_meal else 1
        new_meal_id = f"MEAL_{user_id.split('_')[1]}_{meal_count:03}"

        new_meal = Meal(
            id=new_meal_id,
            user_id=user_id,
            restaurant_id=restaurant_id,
            date=now.date(),
            day=day,
            meal_time=meal_time
        )
        db.session.add(new_meal)

        # --- Logic for creating/updating the Review (as before) ---
        review = Review.query.filter_by(user_id=user_id, restaurant_id=restaurant_id).order_by(Review.date.desc()).first()
        if review:
            review.rating = rating
            review.date = now.date()
        else:
            last_review = Review.query.order_by(Review.id.desc()).first()
            next_id_num = int(last_review.id.split('_')[1]) + 1 if last_review else 1
            new_review_id = f"REV_{next_id_num:03}" # Note: This ID generation is simple; for a larger app, a more robust method is needed.
            review = Review(
                id=new_review_id,
                user_id=user_id,
                restaurant_id=restaurant_id,
                date=now.date(),
                rating=rating
            )
            db.session.add(review)

        db.session.commit()
        return jsonify({'message': 'Rating and meal logged successfully!'}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in /api/rate: {e}")
        return jsonify({'message': 'Server error submitting rating'}), 500

# -----------------------------------------------------------------------
# Debugging Endpoints
# -----------------------------------------------------------------------

@main.route('/api/debug', methods=['GET'])
def debug_config():
    """A utility endpoint to check the live database configuration."""
    configured_db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    return jsonify({
        'message': 'This is the configuration the live app is using.',
        'SQLALCHEMY_DATABASE_URI': configured_db_url
    }), 200
