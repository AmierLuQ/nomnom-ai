# =======================================================================
# app/models.py
# -----------------------------------------------------------------------
# This file contains all the SQLAlchemy database models for the application.
# =======================================================================

from app import db
import datetime

# Each class represents a table in the database.

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
