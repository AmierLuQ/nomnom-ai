# ----------------------------------------------------------------------
# FILE: recommender.py (Advanced Hybrid with Variety & Context)
# ----------------------------------------------------------------------
import pandas as pd
from sqlalchemy import create_engine, text
from math import radians, sin, cos, sqrt, atan2, log
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Dataset, Reader, SVD
from datetime import datetime
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from zoneinfo import ZoneInfo
import random

# --- Database Connection ---
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
engine = create_engine(db_url or 'sqlite:///nomnom.db')

# --- Helper & Context Functions ---
def haversine(lat1, lon1, lat2, lon2):
    if any(v is None or not isinstance(v, (int, float)) for v in [lat1, lon1, lat2, lon2]):
        return float('inf')
    R = 6371; lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2]); dlon = lon2 - lon1; dlat = lat2 - lat1; a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2; c = 2 * atan2(sqrt(a), sqrt(1 - a)); return R * c

def is_restaurant_open(restaurant_row, current_time_float):
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

def get_current_context():
    # FIX: Reverted timezone to Asia/Kuala_Lumpur for production
    malaysia_tz = ZoneInfo("Asia/Kuala_Lumpur")
    now = datetime.now(malaysia_tz)
    day = now.strftime('%A')
    hour = now.hour; minute = now.minute; current_time_float = hour + minute / 60.0
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
    return len(meals_df[meals_df['user_id'] == user_id])

# --- Feature Engineering & Scoring ---
def build_user_profile(user_id, meals_df, restaurants_df, interactions_df):
    user_meals = meals_df[meals_df['user_id'] == user_id]
    if user_meals.empty: return {}
    
    user_meals_details = pd.merge(user_meals, restaurants_df, left_on='restaurant_id', right_on='id', how='left').dropna(subset=['price_min', 'price_max'])
    
    price_min_numeric = pd.to_numeric(user_meals_details['price_min'], errors='coerce')
    price_max_numeric = pd.to_numeric(user_meals_details['price_max'], errors='coerce')
    avg_price = (price_min_numeric.mean() + price_max_numeric.mean()) / 2 if not user_meals_details.empty else 30.0

    weekday_meals = user_meals_details[~user_meals_details['day'].isin(['Saturday', 'Sunday'])]
    weekend_meals = user_meals_details[user_meals_details['day'].isin(['Saturday', 'Sunday'])]
    
    disliked_tags = []
    if not interactions_df.empty and 'user_id' in interactions_df.columns:
        declined_interactions = interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['user_action'] == 'decline')]
        if not declined_interactions.empty:
            declined_details = pd.merge(declined_interactions, restaurants_df, left_on='restaurant_id', right_on='id', how='left')
            disliked_tags = declined_details[['tag_1', 'tag_2', 'tag_3']].stack().value_counts().nlargest(3).index.tolist()

    profile = {
        'top_tags': user_meals_details[['tag_1', 'tag_2', 'tag_3']].stack().mode().tolist(),
        'disliked_tags': disliked_tags, 'avg_price': avg_price,
        'weekday_travel_dist': weekday_meals['distance_travelled'].median() if not weekday_meals.empty and 'distance_travelled' in weekday_meals.columns else 5.0,
        'weekend_travel_dist': weekend_meals['distance_travelled'].median() if not weekend_meals.empty and 'distance_travelled' in weekend_meals.columns else 15.0,
    }
    return profile

def create_implicit_ratings(reviews_df):
    df = reviews_df.copy()
    def calculate_score(row):
        score = float(row['rating'])
        if row.get('price_satisfaction') == True: score += 1.0
        if pd.notna(row.get('visit_frequency')) and row['visit_frequency'] > 2: score += 1.0
        if row.get('price_satisfaction') == False: score -= 0.5
        return min(7.0, max(1.0, score))
    df['implicit_rating'] = df.apply(calculate_score, axis=1)
    return df

def calculate_relevance_score(restaurant, user, user_profile, context, meal_time_appropriateness):
    day, meal_time, _ = context
    score = 0
    weights = {'distance': 0.4, 'price': 0.2, 'tag': 0.2, 'popularity': 0.1, 'appropriateness': 0.1}
    
    is_weekend = day in ['Saturday', 'Sunday']
    expected_dist = user_profile.get('weekend_travel_dist', 15.0) if is_weekend else user_profile.get('weekday_travel_dist', 5.0)
    actual_dist = haversine(user['latitude'], user['longitude'], restaurant['latitude'], restaurant['longitude'])
    score += max(0, 1 - (actual_dist / (expected_dist * 2))) * weights['distance']
    
    restaurant_price = (pd.to_numeric(restaurant['price_min'], errors='coerce') + pd.to_numeric(restaurant['price_max'], errors='coerce')) / 2
    if pd.notna(restaurant_price) and user_profile.get('avg_price'):
        score += max(0, 1 - (abs(restaurant_price - user_profile['avg_price']) / user_profile['avg_price'])) * weights['price']
        
    restaurant_tags = set([t for t in [restaurant['tag_1'], restaurant['tag_2'], restaurant['tag_3']] if pd.notna(t)])
    if user_profile.get('top_tags') and restaurant_tags.intersection(set(user_profile['top_tags'])): score += weights['tag']
    if user_profile.get('disliked_tags') and restaurant_tags.intersection(set(user_profile['disliked_tags'])): score -= 0.3
    
    score += min(1, log((restaurant.get('num_google_reviews') or 0) + 1) / 7) * weights['popularity']
    
    # NEW: Meal-Time Appropriateness Score
    tag_appropriateness_score = 0
    for tag in restaurant_tags:
        tag_appropriateness_score += meal_time_appropriateness.get(tag, 0)
    score += (tag_appropriateness_score / max(1, len(restaurant_tags))) * weights['appropriateness']

    return score

# --- Recommendation Models ---
def recommend_for_new_user(user, restaurants_df, meals_df, exclude_ids=[], context=None):
    if context is None:
        context = get_current_context()
    day, meal_time, current_time_float = context

    # Filter for open restaurants first
    open_restaurants = restaurants_df[restaurants_df.apply(is_restaurant_open, args=(current_time_float,), axis=1)]

    popular_now_ids = meals_df[meals_df['meal_time'] == meal_time]['restaurant_id'].value_counts().nlargest(30).index.tolist()
    open_restaurants['distance'] = open_restaurants.apply(lambda r: haversine(user['latitude'], user['longitude'], r['latitude'], r['longitude']), axis=1)
    nearby_ids = open_restaurants.sort_values('distance').head(30)['id'].tolist()
    
    candidate_ids = list(dict.fromkeys(popular_now_ids + nearby_ids))
    final_rec_ids = [rid for rid in candidate_ids if rid not in exclude_ids]
    return final_rec_ids[:15]

def recommend_for_active_user(user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids=[], context=None):
    if context is None:
        context = get_current_context()
    
    day, meal_time, current_time_float = context
    user_profile = build_user_profile(user['id'], meals_df, restaurants_df, interactions_df)
    
    all_seen_ids = set(exclude_ids)
    if not interactions_df.empty and 'user_id' in interactions_df.columns:
        user_interactions = interactions_df[interactions_df['user_id'] == user['id']]
        all_seen_ids.update(user_interactions['restaurant_id'].unique())
    
    # --- NEW: Content-First Hybrid Strategy ---
    # 1. Get primary recommendations from Content-Based model
    content_candidates = get_content_based_recs(user['id'], restaurants_df, meals_df, all_seen_ids)
    
    # 2. Get discovery items from SVD
    svd_candidates = get_svd_recs(user['id'], reviews_df, restaurants_df, all_seen_ids)
    
    # 3. Blend the lists: Prioritize content, inject discovery
    final_candidates = content_candidates[:10] # Take top 10 content-based
    discovery_items = [item for item in svd_candidates if item not in final_candidates][:5] # Add 5 unique discovery items
    final_candidates.extend(discovery_items)
    random.shuffle(final_candidates) # Shuffle to interleave them

    candidate_details = restaurants_df[restaurants_df['id'].isin(final_candidates)]
    if candidate_details.empty: return []

    open_candidates = candidate_details[candidate_details.apply(is_restaurant_open, args=(current_time_float,), axis=1)]
    if open_candidates.empty: return []

    # NEW: Pre-calculate meal-time appropriateness scores
    meal_time_appropriateness = calculate_meal_time_appropriateness(meals_df, restaurants_df, meal_time)
    
    scored_recs = [(r['id'], calculate_relevance_score(r, user, user_profile, context, meal_time_appropriateness)) for _, r in open_candidates.iterrows()]
    scored_recs.sort(key=lambda x: x[1], reverse=True)
    
    final_rec_ids = [rec_id for rec_id, score in scored_recs if rec_id not in exclude_ids]
    return final_rec_ids[:15]

def get_svd_recs(user_id, reviews_df, restaurants_df, all_seen_ids):
    if reviews_df.empty: return []
    implicit_reviews_df = create_implicit_ratings(reviews_df)
    reader = Reader(rating_scale=(1, 7)); data = Dataset.load_from_df(implicit_reviews_df[['user_id', 'restaurant_id', 'implicit_rating']], reader)
    trainset = data.build_full_trainset(); model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02); model.fit(trainset)
    unseen_ids = set(restaurants_df['id']) - all_seen_ids
    predictions = [model.predict(user_id, rest_id) for rest_id in unseen_ids]
    predictions.sort(key=lambda x: x.est, reverse=True)
    return [pred.iid for pred in predictions[:100]]

def get_content_based_recs(user_id, restaurants_df, meals_df, all_seen_ids):
    user_eaten_restaurants = meals_df[meals_df['user_id'] == user_id]
    eaten_restaurant_ids = user_eaten_restaurants['restaurant_id'].unique()
    if len(eaten_restaurant_ids) == 0: return []

    restaurants_df['tags_combined'] = restaurants_df[['tag_1', 'tag_2', 'tag_3']].fillna('').agg(' '.join, axis=1)
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(restaurants_df['tags_combined'])
    
    user_profile_indices = restaurants_df[restaurants_df['id'].isin(eaten_restaurant_ids)].index
    if len(user_profile_indices) == 0: return []
    
    user_profile_vector = np.asarray(tfidf_matrix[user_profile_indices].mean(axis=0))
    
    cosine_sim = cosine_similarity(user_profile_vector, tfidf_matrix)
    sim_scores = sorted(list(enumerate(cosine_sim[0])), key=lambda x: x[1], reverse=True)
    
    recommended_ids = []
    for idx, score in sim_scores:
        restaurant_id = restaurants_df.iloc[idx]['id']
        if restaurant_id not in all_seen_ids:
            recommended_ids.append(restaurant_id)
        if len(recommended_ids) >= 50:
            break
    return recommended_ids

def calculate_meal_time_appropriateness(meals_df, restaurants_df, current_meal_time):
    """NEW: Analyzes all historical data to see which tags are popular for a given mealtime."""
    if meals_df.empty: return {}
    
    meal_time_data = pd.merge(meals_df, restaurants_df, left_on='restaurant_id', right_on='id', how='left')
    
    # Get tag distribution for the CURRENT mealtime
    current_meal_tags = meal_time_data[meal_time_data['meal_time'] == current_meal_time]
    if current_meal_tags.empty: return {}
    
    tag_counts = current_meal_tags[['tag_1', 'tag_2', 'tag_3']].stack().value_counts()
    
    # Normalize to get a score between 0 and 1
    max_count = tag_counts.max()
    if max_count == 0: return {}
    
    appropriateness_scores = (tag_counts / max_count).to_dict()
    return appropriateness_scores

# --- Main Orchestrator ---
def get_recommendations(user_id, exclude_ids=[]):
    try:
        users_df = pd.read_sql_table('user', engine); reviews_df = pd.read_sql_table('review', engine); restaurants_df = pd.read_sql_table('restaurant', engine); interactions_df = pd.read_sql_table('interaction_log', engine); meals_df = pd.read_sql_table('meal', engine)
    except Exception as e:
        print(f"[ERROR] Failed to load data from database: {e}")
        return []
        
    try:
        current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
    except IndexError: 
        print(f"[ERROR] User {user_id} not found in database.")
        return []

    if not meals_df.empty and not users_df.empty and not restaurants_df.empty:
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
