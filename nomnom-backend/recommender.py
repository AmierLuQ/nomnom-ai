# ----------------------------------------------------------------------
# FILE: recommender.py (Advanced Dynamic & Context-Aware Hybrid Model)
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
    if any(v is None or not isinstance(v, (int, float)) for v in [lat1, lon1, lat2, lon2]): return float('inf')
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
    return day, meal_time

def get_meal_count(user_id, interactions_df):
    return len(interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['user_action'] == 'eat')])

# --- Feature Engineering ---
def build_user_profile(user_id, meals_df, restaurants_df, interactions_df):
    """Builds a rich user profile from their meal and interaction history."""
    user_meals = meals_df[meals_df['user_id'] == user_id]
    if user_meals.empty: return {}
    user_meals_details = pd.merge(user_meals, restaurants_df, left_on='restaurant_id', right_on='id', how='left')
    user_meals_details.dropna(subset=['price_min', 'price_max'], inplace=True)
    
    price_min_numeric = pd.to_numeric(user_meals_details['price_min'], errors='coerce')
    price_max_numeric = pd.to_numeric(user_meals_details['price_max'], errors='coerce')
    avg_price = (price_min_numeric.mean() + price_max_numeric.mean()) / 2 if not user_meals_details.empty else 30.0

    weekday_meals = user_meals_details[~user_meals_details['day'].isin(['Saturday', 'Sunday'])]
    weekend_meals = user_meals_details[user_meals_details['day'].isin(['Saturday', 'Sunday'])]
    
    # NEW: Analyze negative feedback
    declined_interactions = interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['user_action'] == 'decline')]
    if not declined_interactions.empty:
        declined_details = pd.merge(declined_interactions, restaurants_df, left_on='restaurant_id', right_on='id', how='left')
        disliked_tags = declined_details[['tag_1', 'tag_2', 'tag_3']].stack().value_counts().nlargest(3).index.tolist()
    else:
        disliked_tags = []

    profile = {
        'top_tags': user_meals_details[['tag_1', 'tag_2', 'tag_3']].stack().mode().tolist(),
        'disliked_tags': disliked_tags,
        'avg_price': avg_price,
        'weekday_travel_dist': weekday_meals['distance_travelled'].median() if not weekday_meals.empty else 5.0,
        'weekend_travel_dist': weekend_meals['distance_travelled'].median() if not weekend_meals.empty else 15.0,
    }
    return profile

def create_implicit_ratings(reviews_df):
    """Creates a more nuanced 'implicit_rating' based on multiple feedback signals."""
    df = reviews_df.copy()
    
    def calculate_score(row):
        score = float(row['rating'])
        # Boost score for price satisfaction and high frequency
        if row['price_satisfaction'] == True and pd.notna(row['price_satisfaction']):
            score += 1.0
        if pd.notna(row['visit_frequency']) and row['visit_frequency'] > 2:
            score += 1.0
        # Penalize for price dissatisfaction
        if row['price_satisfaction'] == False and pd.notna(row['price_satisfaction']):
            score -= 0.5
        return min(7.0, max(1.0, score)) # Clamp score between 1 and 7

    df['implicit_rating'] = df.apply(calculate_score, axis=1)
    return df

# --- Scoring Functions ---
def calculate_relevance_score(restaurant, user, user_profile, context, predicted_tag):
    """Calculates a holistic score with dynamic weights and pattern recognition."""
    day, meal_time = context
    score = 0
    weights = {'distance': 0.3, 'price': 0.2, 'tag': 0.2, 'popularity': 0.1, 'pattern': 0.2} # Base weights

    # 1. Dynamic Distance Score
    is_weekend = day in ['Saturday', 'Sunday']
    expected_dist = user_profile.get('weekend_travel_dist', 15.0) if is_weekend else user_profile.get('weekday_travel_dist', 5.0)
    if expected_dist > 20: weights['distance'] = 0.2 # User is a traveler, distance is less important
    actual_dist = haversine(user['latitude'], user['longitude'], restaurant['latitude'], restaurant['longitude'])
    distance_score = max(0, 1 - (actual_dist / (expected_dist * 2))) # Less harsh penalty for going over
    score += distance_score * weights['distance']

    # 2. Dynamic Price Score
    if user_profile.get('avg_price', 0) < 20: weights['price'] = 0.3 # User is price sensitive
    restaurant_price = (pd.to_numeric(restaurant['price_min'], errors='coerce') + pd.to_numeric(restaurant['price_max'], errors='coerce')) / 2
    if pd.notna(restaurant_price) and user_profile.get('avg_price'):
        price_diff = abs(restaurant_price - user_profile['avg_price']) / user_profile['avg_price']
        price_score = max(0, 1 - price_diff)
        score += price_score * weights['price']

    # 3. Tag Score (Positive and Negative)
    restaurant_tags = set([t for t in [restaurant['tag_1'], restaurant['tag_2'], restaurant['tag_3']] if pd.notna(t)])
    if user_profile.get('top_tags'):
        profile_tags = set(user_profile['top_tags'])
        if restaurant_tags.intersection(profile_tags): score += weights['tag']
    if user_profile.get('disliked_tags'):
        disliked_tags = set(user_profile['disliked_tags'])
        if restaurant_tags.intersection(disliked_tags): score -= 0.3 # Heavy penalty for disliked tags

    # 4. Popularity Score
    popularity = log((restaurant.get('num_google_reviews') or 0) + 1)
    normalized_popularity = min(1, popularity / 7)
    score += normalized_popularity * weights['popularity']
    
    # 5. Pattern Recognition Score
    if predicted_tag and predicted_tag in restaurant_tags:
        score += weights['pattern'] # Add bonus if it matches the predicted pattern

    return score

# --- Recommendation Models ---
def recommend_for_new_user(user, restaurants_df, meals_df, exclude_ids=[]):
    # This model is now enhanced in the main orchestrator, no changes needed here.
    return recommend_for_active_user(user, restaurants_df, None, None, meals_df, exclude_ids, is_new_user=True)

def recommend_for_active_user(user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids=[], is_new_user=False):
    print(f"Running model for user {user['id']} (New User: {is_new_user})")
    context = get_current_context()
    
    # Step 1: Feature Engineering
    user_profile = build_user_profile(user['id'], meals_df, restaurants_df, interactions_df)
    
    # Step 2: Pattern Recognition (for warm-start users)
    predicted_tag = None
    if not is_new_user:
        pattern_model, encoders = train_pattern_recognition_model(user['id'], meals_df, restaurants_df)
        if pattern_model:
            try:
                day_encoded = encoders['day'].transform([context[0]])[0]
                meal_time_encoded = encoders['meal_time'].transform([context[1]])[0]
                predicted_tag_encoded = pattern_model.predict([[day_encoded, meal_time_encoded]])[0]
                predicted_tag = encoders['tag'].inverse_transform([predicted_tag_encoded])[0]
                print(f"Pattern model predicts user is in the mood for: {predicted_tag}")
            except Exception as e:
                print(f"Could not predict tag: {e}")

    # Step 3: Candidate Generation
    if is_new_user: # Cold-start candidates
        day, meal_time = context
        popular_now_ids = meals_df[meals_df['meal_time'] == meal_time]['restaurant_id'].value_counts().nlargest(30).index.tolist()
        restaurants_df['distance'] = restaurants_df.apply(lambda row: haversine(user['latitude'], user['longitude'], row['latitude'], row['longitude']), axis=1)
        nearby_ids = restaurants_df.sort_values('distance').head(30)['id'].tolist()
        candidate_ids = list(dict.fromkeys(popular_now_ids + nearby_ids))
    else: # Warm-start candidates from SVD
        all_seen_ids = set(interactions_df[(interactions_df['user_id'] == user['id'])]['restaurant_id'].unique()) | set(exclude_ids)
        candidate_ids = get_svd_recs(user['id'], reviews_df, restaurants_df, all_seen_ids)

    # Step 4: Scoring and Ranking
    candidate_details = restaurants_df[restaurants_df['id'].isin(candidate_ids)]
    scored_recs = []
    for _, restaurant in candidate_details.iterrows():
        score = calculate_relevance_score(restaurant, user, user_profile, context, predicted_tag)
        scored_recs.append((restaurant['id'], score))
        
    scored_recs.sort(key=lambda x: x[1], reverse=True)
    final_rec_ids = [rec_id for rec_id, score in scored_recs if rec_id not in exclude_ids]
    return final_rec_ids[:15]

def get_svd_recs(user_id, reviews_df, restaurants_df, all_seen_ids):
    if reviews_df.empty: return []
    
    # Use implicit ratings
    implicit_reviews_df = create_implicit_ratings(reviews_df)
    reader = Reader(rating_scale=(1, 7)) # Adjusted scale
    data = Dataset.load_from_df(implicit_reviews_df[['user_id', 'restaurant_id', 'implicit_rating']], reader)
    trainset = data.build_full_trainset()
    model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02)
    model.fit(trainset)
    
    unseen_ids = set(restaurants_df['id']) - all_seen_ids
    predictions = [model.predict(user_id, rest_id) for rest_id in unseen_ids]
    predictions.sort(key=lambda x: x.est, reverse=True)
    return [pred.iid for pred in predictions[:50]]

def train_pattern_recognition_model(user_id, meals_df, restaurants_df):
    """Trains a Decision Tree to learn a user's contextual tag preferences."""
    user_meals = meals_df[meals_df['user_id'] == user_id]
    if len(user_meals) < 10: return None, None # Not enough data to train
    
    training_data = pd.merge(user_meals, restaurants_df, left_on='restaurant_id', right_on='id')
    training_data = training_data[['day', 'meal_time', 'tag_1']].dropna()
    if len(training_data) < 10: return None, None

    # Encode categorical features
    encoders = {
        'day': LabelEncoder().fit(training_data['day']),
        'meal_time': LabelEncoder().fit(training_data['meal_time']),
        'tag': LabelEncoder().fit(training_data['tag_1'])
    }
    
    X = pd.DataFrame({
        'day': encoders['day'].transform(training_data['day']),
        'meal_time': encoders['meal_time'].transform(training_data['meal_time'])
    })
    y = encoders['tag'].transform(training_data['tag_1'])
    
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X, y)
    return model, encoders

# --- Main Orchestrator ---
def get_recommendations(user_id, exclude_ids=[]):
    users_df = pd.read_sql_table('user', engine)
    reviews_df = pd.read_sql_table('review', engine)
    restaurants_df = pd.read_sql_table('restaurant', engine)
    interactions_df = pd.read_sql_table('interaction_log', engine)
    meals_df = pd.read_sql_table('meal', engine)
    
    try:
        current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
    except IndexError: return []

    # Pre-calculate distance travelled for all meals
    if not meals_df.empty:
        meals_with_loc = pd.merge(meals_df, users_df[['id', 'latitude', 'longitude']], left_on='user_id', right_on='id')
        meals_with_loc = pd.merge(meals_with_loc, restaurants_df[['id', 'latitude', 'longitude']], left_on='restaurant_id', right_on='id', suffixes=('_user', '_rest'))
        meals_df['distance_travelled'] = meals_with_loc.apply(lambda row: haversine(row['latitude_user'], row['longitude_user'], row['latitude_rest'], row['longitude_rest']), axis=1)

    meal_count = get_meal_count(user_id, interactions_df)
    
    if meal_count < 15:
        return recommend_for_new_user(current_user, restaurants_df, meals_df, exclude_ids)
    else:
        return recommend_for_active_user(current_user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids)
