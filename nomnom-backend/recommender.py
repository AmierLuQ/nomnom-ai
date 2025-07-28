# =======================================================================
# recommender.py (Reverted to Robust Scoring Model)
# -----------------------------------------------------------------------
# This version brings back the more robust scoring and profiling logic
# that was performing better in earlier tests, and fixes the cold-start logic.
# =======================================================================

# Standard library imports
import os
import datetime
from math import radians, sin, cos, sqrt, atan2, log
from zoneinfo import ZoneInfo

# Third-party imports
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from surprise import Dataset, Reader, SVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

# --- Database Connection ---
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
engine = create_engine(db_url or 'sqlite:///nomnom.db')

# =======================================================================
# Helper & Context Functions
# =======================================================================

def haversine(lat1, lon1, lat2, lon2):
    """Calculates the distance between two lat/lon points in kilometers."""
    if any(v is None or not isinstance(v, (int, float)) for v in [lat1, lon1, lat2, lon2]):
        return float('inf')
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def is_restaurant_open(restaurant_row, current_time_float):
    """Checks if a restaurant is open based on the current time."""
    opening_time_str = restaurant_row['opening_time']
    closing_time_str = restaurant_row['closing_time']
    if pd.isna(opening_time_str) or pd.isna(closing_time_str): return True
    if opening_time_str == closing_time_str: return True
    try:
        open_hour, open_min, _ = map(int, opening_time_str.split(':'))
        close_hour, close_min, _ = map(int, closing_time_str.split(':'))
        open_time_float = open_hour + open_min / 60.0
        close_time_float = close_hour + close_min / 60.0
        if close_time_float < open_time_float:
            return current_time_float >= open_time_float or current_time_float < close_time_float
        else:
            return open_time_float <= current_time_float < close_time_float
    except (ValueError, TypeError):
        return True

def get_current_context(context_override=None):
    """Gets the current day, mealtime, and float time, using an override for testing."""
    if context_override:
        return context_override

    malaysia_tz = ZoneInfo("Asia/Kuala_Lumpur")
    now = datetime.datetime.now(malaysia_tz)
    day = now.strftime('%A')
    current_time_float = now.hour + now.minute / 60.0
    
    if 4.0 <= current_time_float < 7.0: meal_time = "Suhoor"
    elif 7.0 <= current_time_float < 10.0: meal_time = "Breakfast"
    elif 10.0 <= current_time_float < 12.0: meal_time = "Brunch"
    elif 12.0 <= current_time_float < 16.0: meal_time = "Lunch"
    elif 16.0 <= current_time_float < 17.5: meal_time = "Tea Time"
    elif 17.5 <= current_time_float < 19.5: meal_time = "Linner"
    elif 19.5 <= current_time_float < 22.0: meal_time = "Dinner"
    elif 22.0 <= current_time_float < 23.5: meal_time = "Late Dinner"
    else: meal_time = "Midnight Snack"
    
    return day, meal_time, current_time_float

def get_meal_count(user_id, meals_df):
    """Counts meals for a user from the provided dataframe."""
    return len(meals_df[meals_df['user_id'] == user_id])

# =======================================================================
# Feature Engineering & Scoring
# =======================================================================

def build_user_profile(user_id, meals_df, restaurants_df):
    """Builds a detailed profile of a user's tastes and habits."""
    user_meals = meals_df[meals_df['user_id'] == user_id]
    if user_meals.empty: return {}
    
    user_meals_details = pd.merge(user_meals, restaurants_df, left_on='restaurant_id', right_on='id', how='left')
    
    price_meals = user_meals_details.dropna(subset=['price_min', 'price_max'])
    price_min_numeric = pd.to_numeric(price_meals['price_min'], errors='coerce')
    price_max_numeric = pd.to_numeric(price_meals['price_max'], errors='coerce')
    avg_price = (price_min_numeric.mean() + price_max_numeric.mean()) / 2 if not price_meals.empty else 30.0

    weekday_meals = user_meals_details[~user_meals_details['day'].isin(['Saturday', 'Sunday'])]
    weekend_meals = user_meals_details[user_meals_details['day'].isin(['Saturday', 'Sunday'])]
    
    profile = {
        'top_tags': user_meals_details[['tag_1', 'tag_2', 'tag_3']].stack().mode().tolist(),
        'avg_price': avg_price,
        'weekday_travel_dist': weekday_meals['distance_travelled'].median() if not weekday_meals.empty and 'distance_travelled' in weekday_meals.columns else 5.0,
        'weekend_travel_dist': weekend_meals['distance_travelled'].median() if not weekend_meals.empty and 'distance_travelled' in weekend_meals.columns else 15.0,
    }
    return profile

def calculate_relevance_score(restaurant, user, user_profile, context, user_eaten_ids):
    """Calculates a relevance score based on a stable set of weights."""
    day, _, _ = context
    score = 0.0
    weights = {'distance': 0.4, 'price': 0.2, 'tag': 0.3, 'popularity': 0.1}

    is_weekend = day in ['Saturday', 'Sunday']
    expected_dist = user_profile.get('weekend_travel_dist', 15.0) if is_weekend else user_profile.get('weekday_travel_dist', 5.0)
    actual_dist = haversine(user['latitude'], user['longitude'], restaurant['latitude'], restaurant['longitude'])
    distance_score = max(0, 1 - (actual_dist / (expected_dist * 1.5)))
    score += distance_score * weights['distance']

    restaurant_price = (pd.to_numeric(restaurant['price_min'], errors='coerce') + pd.to_numeric(restaurant['price_max'], errors='coerce')) / 2
    if pd.notna(restaurant_price) and user_profile.get('avg_price'):
        price_diff = abs(restaurant_price - user_profile['avg_price']) / user_profile['avg_price']
        price_score = max(0, 1 - price_diff)
        score += price_score * weights['price']

    restaurant_tags = set([t for t in [restaurant['tag_1'], restaurant['tag_2'], restaurant['tag_3']] if pd.notna(t)])
    if user_profile.get('top_tags') and restaurant_tags.intersection(set(user_profile['top_tags'])):
        score += weights['tag']

    popularity = log((restaurant.get('num_google_reviews') or 0) + 1)
    normalized_popularity = min(1, popularity / 7)
    score += normalized_popularity * weights['popularity']
    
    # --- NEW: Revisit Penalty ---
    # Apply a small penalty if the user has already eaten at this restaurant.
    if restaurant['id'] in user_eaten_ids:
        score *= 0.8  # e.g., reduce the score by 20%
    
    return score

# =======================================================================
# Recommendation Models
# =======================================================================

def get_content_based_recs(user_id, restaurants_df, meals_df):
    """Generates recommendations based on the content (tags) of a user's meal history."""
    user_meals = meals_df[meals_df['user_id'] == user_id]
    eaten_ids = user_meals['restaurant_id'].unique()
    if len(eaten_ids) == 0: return []

    restaurants_df['tags_combined'] = restaurants_df[['tag_1', 'tag_2', 'tag_3']].fillna('').agg(' '.join, axis=1)
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(restaurants_df['tags_combined'])
    
    user_profile_indices = restaurants_df[restaurants_df['id'].isin(eaten_ids)].index
    if len(user_profile_indices) == 0: return []
    
    user_profile_vector = np.asarray(tfidf_matrix[user_profile_indices].mean(axis=0))
    cosine_sim = cosine_similarity(user_profile_vector, tfidf_matrix)
    sim_scores = sorted(list(enumerate(cosine_sim[0])), key=lambda x: x[1], reverse=True)
    
    # Return all ranked restaurants, filtering will happen later
    return [restaurants_df.iloc[idx]['id'] for idx, score in sim_scores]

def recommend_for_new_user(user, restaurants_df, meals_df, exclude_ids=[], context=None):
    """Generates recommendations for new users based on popularity and proximity."""
    if context is None:
        context = get_current_context()
    day, meal_time, current_time_float = context

    popular_now_ids = meals_df[meals_df['meal_time'] == meal_time]['restaurant_id'].value_counts().nlargest(30).index.tolist()
    
    restaurants_df['distance'] = restaurants_df.apply(lambda r: haversine(user['latitude'], user['longitude'], r['latitude'], r['longitude']), axis=1)
    nearby_ids = restaurants_df.sort_values('distance').head(30)['id'].tolist()
    
    candidate_ids = list(dict.fromkeys(popular_now_ids + nearby_ids))
    
    candidate_details = restaurants_df[restaurants_df['id'].isin(candidate_ids)]
    if candidate_details.empty: return []

    open_candidates = candidate_details[candidate_details.apply(is_restaurant_open, args=(current_time_float,), axis=1)]
    if open_candidates.empty: return []

    open_candidates['popularity'] = open_candidates['num_google_reviews'].fillna(0)
    ranked_recs = open_candidates.sort_values('popularity', ascending=False)
    
    final_rec_ids = [rid for rid in ranked_recs['id'] if rid not in exclude_ids]
    return final_rec_ids[:15]


def recommend_for_active_user(user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids=[], context=None):
    """Main recommendation logic for an active user."""
    if context is None:
        context = get_current_context()
    
    user_profile = build_user_profile(user['id'], meals_df, restaurants_df)
    
    user_eaten_ids = set(meals_df[meals_df['user_id'] == user['id']]['restaurant_id'])
    
    # --- FIX: Generate candidates without pre-filtering eaten restaurants ---
    candidate_ids = get_content_based_recs(user['id'], restaurants_df, meals_df)

    candidate_details = restaurants_df[restaurants_df['id'].isin(candidate_ids)]
    if candidate_details.empty: return []

    open_candidates = candidate_details[candidate_details.apply(is_restaurant_open, args=(context[2],), axis=1)]
    if open_candidates.empty: return []
    
    scored_recs = []
    for _, restaurant in open_candidates.iterrows():
        # --- FIX: Pass user_eaten_ids to the scoring function ---
        score = calculate_relevance_score(restaurant, user, user_profile, context, user_eaten_ids)
        scored_recs.append((restaurant['id'], score))
        
    scored_recs.sort(key=lambda x: x[1], reverse=True)
    
    # Filter out restaurants from the current session (exclude_ids) at the very end
    final_rec_ids = [rec_id for rec_id, score in scored_recs if rec_id not in exclude_ids]
    
    return final_rec_ids[:15]

# =======================================================================
# Main Orchestrator
# =======================================================================

def get_recommendations(user_id, exclude_ids=[]):
    """Loads data and routes the request to the correct model."""
    try:
        users_df = pd.read_sql_table('user', engine)
        reviews_df = pd.read_sql_table('review', engine)
        restaurants_df = pd.read_sql_table('restaurant', engine)
        meals_df = pd.read_sql_table('meal', engine)
        interactions_df = pd.read_sql_table('interaction_log', engine)
    except Exception as e:
        print(f"[ERROR] Failed to load data from database: {e}")
        return []

    try:
        current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
    except IndexError: 
        print(f"[ERROR] User {user_id} not found in database.")
        return []

    if not meals_df.empty:
        user_locs = users_df.set_index('id')[['latitude', 'longitude']].to_dict('index')
        rest_locs = restaurants_df.set_index('id')[['latitude', 'longitude']].to_dict('index')
        meals_df['user_lat'] = meals_df['user_id'].map(lambda x: user_locs.get(x, {}).get('latitude'))
        meals_df['user_lon'] = meals_df['user_id'].map(lambda x: user_locs.get(x, {}).get('longitude'))
        meals_df['rest_lat'] = meals_df['restaurant_id'].map(lambda x: rest_locs.get(x, {}).get('latitude'))
        meals_df['rest_lon'] = meals_df['restaurant_id'].map(lambda x: rest_locs.get(x, {}).get('longitude'))
        meals_df['distance_travelled'] = meals_df.apply(lambda r: haversine(r['user_lat'], r['user_lon'], r['rest_lat'], r['rest_lon']), axis=1)
        meals_df.drop(columns=['user_lat', 'user_lon', 'rest_lat', 'rest_lon'], inplace=True)
    
    meal_count = get_meal_count(user_id, meals_df)
    
    if meal_count < 15:
        return recommend_for_new_user(current_user, restaurants_df, meals_df, exclude_ids)
    else:
        return recommend_for_active_user(current_user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids)
