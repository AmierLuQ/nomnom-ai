# ----------------------------------------------------------------------
# FILE: recommender.py (With Extensive Debug Logging)
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

def get_current_context():
    now = datetime.now()
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
    print(f"[DEBUG] Current context: Day={day}, MealTime={meal_time}")
    return day, meal_time

def get_meal_count(user_id, interactions_df):
    count = len(interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['user_action'] == 'eat')])
    print(f"[DEBUG] User {user_id} has {count} 'eat' interactions.")
    return count

# --- Feature Engineering ---
def build_user_profile(user_id, meals_df, restaurants_df, interactions_df):
    print(f"[DEBUG] Building profile for user {user_id}...")
    user_meals = meals_df[meals_df['user_id'] == user_id]
    if user_meals.empty: 
        print("[DEBUG] User has no meal data. Returning empty profile.")
        return {}
    
    user_meals_details = pd.merge(user_meals, restaurants_df, left_on='restaurant_id', right_on='id', how='left')
    user_meals_details.dropna(subset=['price_min', 'price_max'], inplace=True)
    
    price_min_numeric = pd.to_numeric(user_meals_details['price_min'], errors='coerce')
    price_max_numeric = pd.to_numeric(user_meals_details['price_max'], errors='coerce')
    avg_price = (price_min_numeric.mean() + price_max_numeric.mean()) / 2 if not user_meals_details.empty else 30.0

    weekday_meals = user_meals_details[~user_meals_details['day'].isin(['Saturday', 'Sunday'])]
    weekend_meals = user_meals_details[user_meals_details['day'].isin(['Saturday', 'Sunday'])]
    
    declined_interactions = interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['user_action'] == 'decline')]
    disliked_tags = []
    if not declined_interactions.empty:
        declined_details = pd.merge(declined_interactions, restaurants_df, left_on='restaurant_id', right_on='id', how='left')
        disliked_tags = declined_details[['tag_1', 'tag_2', 'tag_3']].stack().value_counts().nlargest(3).index.tolist()

    profile = {
        'top_tags': user_meals_details[['tag_1', 'tag_2', 'tag_3']].stack().mode().tolist(),
        'disliked_tags': disliked_tags,
        'avg_price': avg_price,
        'weekday_travel_dist': weekday_meals['distance_travelled'].median() if not weekday_meals.empty and 'distance_travelled' in weekday_meals.columns else 5.0,
        'weekend_travel_dist': weekend_meals['distance_travelled'].median() if not weekend_meals.empty and 'distance_travelled' in weekend_meals.columns else 15.0,
    }
    print(f"[DEBUG] Profile built: {profile}")
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

# --- Scoring Functions ---
def calculate_relevance_score(restaurant, user, user_profile, context, predicted_tag):
    # This function is called many times, so logging is kept minimal
    day, meal_time = context
    score = 0
    weights = {'distance': 0.3, 'price': 0.2, 'tag': 0.2, 'popularity': 0.1, 'pattern': 0.2}

    is_weekend = day in ['Saturday', 'Sunday']
    expected_dist = user_profile.get('weekend_travel_dist', 15.0) if is_weekend else user_profile.get('weekday_travel_dist', 5.0)
    if expected_dist > 20: weights['distance'] = 0.2
    actual_dist = haversine(user['latitude'], user['longitude'], restaurant['latitude'], restaurant['longitude'])
    distance_score = max(0, 1 - (actual_dist / (expected_dist * 2)))
    score += distance_score * weights['distance']

    if user_profile.get('avg_price', 0) < 20: weights['price'] = 0.3
    restaurant_price = (pd.to_numeric(restaurant['price_min'], errors='coerce') + pd.to_numeric(restaurant['price_max'], errors='coerce')) / 2
    if pd.notna(restaurant_price) and user_profile.get('avg_price'):
        price_diff = abs(restaurant_price - user_profile['avg_price']) / user_profile['avg_price']
        price_score = max(0, 1 - price_diff)
        score += price_score * weights['price']

    restaurant_tags = set([t for t in [restaurant['tag_1'], restaurant['tag_2'], restaurant['tag_3']] if pd.notna(t)])
    if user_profile.get('top_tags'):
        if restaurant_tags.intersection(set(user_profile['top_tags'])): score += weights['tag']
    if user_profile.get('disliked_tags'):
        if restaurant_tags.intersection(set(user_profile['disliked_tags'])): score -= 0.3

    popularity = log((restaurant.get('num_google_reviews') or 0) + 1)
    normalized_popularity = min(1, popularity / 7)
    score += normalized_popularity * weights['popularity']
    
    if predicted_tag and predicted_tag in restaurant_tags:
        score += weights['pattern']

    return score

# --- Recommendation Models ---
def recommend_for_new_user(user, restaurants_df, meals_df, exclude_ids=[]):
    return recommend_for_active_user(user, restaurants_df, pd.DataFrame(), pd.DataFrame(), meals_df, exclude_ids, is_new_user=True)

def recommend_for_active_user(user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids=[], is_new_user=False):
    print(f"[DEBUG] Running model for user {user['id']} (New User: {is_new_user})")
    context = get_current_context()
    
    user_profile = build_user_profile(user['id'], meals_df, restaurants_df, interactions_df)
    
    predicted_tag = None
    if not is_new_user and not meals_df.empty:
        pattern_model, encoders = train_pattern_recognition_model(user['id'], meals_df, restaurants_df)
        if pattern_model:
            try:
                day_encoded = encoders['day'].transform([context[0]])[0]
                meal_time_encoded = encoders['meal_time'].transform([context[1]])[0]
                predicted_tag_encoded = pattern_model.predict([[day_encoded, meal_time_encoded]])[0]
                predicted_tag = encoders['tag'].inverse_transform([predicted_tag_encoded])[0]
                print(f"[DEBUG] Pattern model predicts user is in the mood for: {predicted_tag}")
            except Exception as e:
                print(f"[DEBUG] Could not predict tag: {e}")

    if is_new_user:
        day, meal_time = context
        popular_now_ids = meals_df[meals_df['meal_time'] == meal_time]['restaurant_id'].value_counts().nlargest(30).index.tolist()
        restaurants_df['distance'] = restaurants_df.apply(lambda row: haversine(user['latitude'], user['longitude'], row['latitude'], row['longitude']), axis=1)
        nearby_ids = restaurants_df.sort_values('distance').head(30)['id'].tolist()
        candidate_ids = list(dict.fromkeys(popular_now_ids + nearby_ids))
        print(f"[DEBUG] Cold-start generated {len(candidate_ids)} candidates.")
    else:
        all_seen_ids = set(interactions_df[(interactions_df['user_id'] == user['id'])]['restaurant_id'].unique()) | set(exclude_ids)
        candidate_ids = get_svd_recs(user['id'], reviews_df, restaurants_df, all_seen_ids)
        print(f"[DEBUG] Warm-start (SVD) generated {len(candidate_ids)} candidates.")

    candidate_details = restaurants_df[restaurants_df['id'].isin(candidate_ids)]
    if candidate_details.empty: 
        print("[DEBUG] No candidate details found after generation. Returning empty list.")
        return []
    
    scored_recs = []
    for _, restaurant in candidate_details.iterrows():
        score = calculate_relevance_score(restaurant, user, user_profile, context, predicted_tag)
        scored_recs.append((restaurant['id'], score))
        
    scored_recs.sort(key=lambda x: x[1], reverse=True)
    
    # Log the top 5 scored recommendations to see what the scores look like
    print(f"[DEBUG] Top 5 scored recommendations: {scored_recs[:5]}")
    
    final_rec_ids = [rec_id for rec_id, score in scored_recs if rec_id not in exclude_ids]
    print(f"[DEBUG] Returning {len(final_rec_ids[:15])} final recommendations.")
    return final_rec_ids[:15]

def get_svd_recs(user_id, reviews_df, restaurants_df, all_seen_ids):
    if reviews_df.empty: 
        print("[DEBUG] SVD model: reviews_df is empty. Cannot generate candidates.")
        return []
    implicit_reviews_df = create_implicit_ratings(reviews_df)
    reader = Reader(rating_scale=(1, 7))
    data = Dataset.load_from_df(implicit_reviews_df[['user_id', 'restaurant_id', 'implicit_rating']], reader)
    trainset = data.build_full_trainset()
    model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02)
    model.fit(trainset)
    unseen_ids = set(restaurants_df['id']) - all_seen_ids
    predictions = [model.predict(user_id, rest_id) for rest_id in unseen_ids]
    predictions.sort(key=lambda x: x.est, reverse=True)
    return [pred.iid for pred in predictions[:50]]

def train_pattern_recognition_model(user_id, meals_df, restaurants_df):
    user_meals = meals_df[meals_df['user_id'] == user_id]
    if len(user_meals) < 10: 
        print("[DEBUG] Not enough data to train pattern model.")
        return None, None
    
    training_data = pd.merge(user_meals, restaurants_df, left_on='restaurant_id', right_on='id')
    training_data = training_data[['day', 'meal_time', 'tag_1']].dropna()
    if len(training_data) < 10: 
        print("[DEBUG] Not enough clean data to train pattern model after merge.")
        return None, None

    encoders = {
        'day': LabelEncoder().fit(training_data['day']),
        'meal_time': LabelEncoder().fit(training_data['meal_time']),
        'tag': LabelEncoder().fit(training_data['tag_1'])
    }
    X = pd.DataFrame({'day': encoders['day'].transform(training_data['day']), 'meal_time': encoders['meal_time'].transform(training_data['meal_time'])})
    y = encoders['tag'].transform(training_data['tag_1'])
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X, y)
    print("[DEBUG] Pattern recognition model trained successfully.")
    return model, encoders

# --- Main Orchestrator ---
def get_recommendations(user_id, exclude_ids=[]):
    print(f"\n--- Starting new recommendation request for user {user_id} ---")
    try:
        users_df = pd.read_sql_table('user', engine)
        reviews_df = pd.read_sql_table('review', engine)
        restaurants_df = pd.read_sql_table('restaurant', engine)
        interactions_df = pd.read_sql_table('interaction_log', engine)
        meals_df = pd.read_sql_table('meal', engine)
        print(f"[DEBUG] Data loaded: {len(users_df)} users, {len(restaurants_df)} restaurants, {len(meals_df)} meals, {len(reviews_df)} reviews.")
    except Exception as e:
        print(f"[ERROR] Failed to load data from database: {e}")
        return []
    
    try:
        current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
    except IndexError: 
        print(f"[ERROR] User {user_id} not found in database.")
        return []

    if not meals_df.empty:
        meals_with_loc = pd.merge(meals_df, users_df[['id', 'latitude', 'longitude']], left_on='user_id', right_on='id', how='left')
        meals_with_loc = pd.merge(meals_with_loc, restaurants_df[['id', 'latitude', 'longitude']], left_on='restaurant_id', right_on='id', how='left', suffixes=('_user', '_rest'))
        meals_with_loc.dropna(subset=['latitude_user', 'longitude_user', 'latitude_rest', 'longitude_rest'], inplace=True)
        
        if not meals_with_loc.empty:
            distances = meals_with_loc.apply(lambda row: haversine(row['latitude_user'], row['longitude_user'], row['latitude_rest'], row['longitude_rest']), axis=1)
            # Use original meal_df index to map distances
            meals_df['distance_travelled'] = distances
        else:
            print("[DEBUG] No meals with complete location data found to calculate distances.")
    else:
        print("[DEBUG] meals_df is empty. Skipping distance calculation.")

    meal_count = get_meal_count(user_id, interactions_df)
    
    if meal_count < 15:
        return recommend_for_new_user(current_user, restaurants_df, meals_df, exclude_ids)
    else:
        return recommend_for_active_user(current_user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids)
