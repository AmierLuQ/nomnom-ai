# ----------------------------------------------------------------------
# FILE: recommender.py (Advanced Context-Aware Hybrid Model)
# ----------------------------------------------------------------------
import pandas as pd
from sqlalchemy import create_engine, text
from math import radians, sin, cos, sqrt, atan2, log
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Dataset, Reader, SVD
from datetime import datetime

# --- Database Connection ---
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
engine = create_engine(db_url or 'sqlite:///nomnom.db')

# --- Helper Functions ---
def haversine(lat1, lon1, lat2, lon2):
    if any(v is None for v in [lat1, lon1, lat2, lon2]): return float('inf')
    R = 6371; lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2]); dlon = lon2 - lon1; dlat = lat2 - lat1; a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2; c = 2 * atan2(sqrt(a), sqrt(1 - a)); return R * c

# --- MODIFIED FUNCTION ---
def get_current_context():
    """Determines the current day of the week and mealtime based on a detailed schedule."""
    now = datetime.now()
    day = now.strftime('%A')  # e.g., 'Monday'
    hour = now.hour
    minute = now.minute
    
    # Convert current time to a float for easier comparison (e.g., 9:30 -> 9.5)
    current_time = hour + minute / 60.0

    if 4.0 <= current_time < 7.0:
        meal_time = "Suhoor"
    elif 7.0 <= current_time < 10.0:
        meal_time = "Breakfast"
    elif 10.0 <= current_time < 12.0:
        meal_time = "Brunch"
    elif 12.0 <= current_time < 16.0:
        meal_time = "Lunch"
    elif 16.0 <= current_time < 17.5:
        meal_time = "Tea Time"
    elif 17.5 <= current_time < 19.5:
        meal_time = "Linner"
    elif 19.5 <= current_time < 22.0:
        meal_time = "Dinner"
    elif 22.0 <= current_time < 23.5:
        meal_time = "Late Dinner"
    else:  # Handles the overnight case for Midnight Snack (23.5 to 4.0)
        meal_time = "Midnight Snack"
        
    return day, meal_time

def get_meal_count(user_id, interactions_df):
    return len(interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['user_action'] == 'eat')])

# --- Cold-Start Model ---
def recommend_for_new_user(user, restaurants_df, meals_df, exclude_ids=[]):
    """
    For new users, recommend restaurants that are popular for the current mealtime
    and are located nearby.
    """
    print("Running Cold-Start Model with Contextual Popularity.")
    _, current_meal_time = get_current_context()

    # Find restaurants popular during the current mealtime
    popular_now = meals_df[meals_df['meal_time'] == current_meal_time]['restaurant_id'].value_counts().nlargest(30).index.tolist()
    
    # Filter the main restaurant list to these popular ones
    contextual_restaurants = restaurants_df[restaurants_df['id'].isin(popular_now)].copy()

    # Calculate distance for each of these restaurants from the user
    contextual_restaurants['distance'] = contextual_restaurants.apply(
        lambda row: haversine(user['latitude'], user['longitude'], row['latitude'], row['longitude']), axis=1
    )
    
    # Calculate a popularity score
    contextual_restaurants['popularity_score'] = contextual_restaurants['google_rating'] * contextual_restaurants['num_google_reviews'].apply(lambda x: log(x + 1 if pd.notna(x) else 1))
    
    # Sort by distance (closer is better) and popularity
    sorted_recs = contextual_restaurants.sort_values(by=['distance', 'popularity_score'], ascending=[True, False])
    
    all_recs = sorted_recs['id'].tolist()
    filtered_recs = [rec for rec in all_recs if rec not in exclude_ids]
    return filtered_recs[:15]

# --- Warm-Start Model Components ---
def build_user_profile(user_id, meals_df, restaurants_df):
    """Analyzes a user's meal history to build a detailed taste profile."""
    user_meals = meals_df[meals_df['user_id'] == user_id]
    if user_meals.empty: return {}

    # Merge with restaurant data to get tags and prices
    user_meals_details = pd.merge(user_meals, restaurants_df, left_on='restaurant_id', right_on='id')

    profile = {
        'top_meal_time': user_meals['meal_time'].mode()[0] if not user_meals['meal_time'].mode().empty else None,
        'top_day': user_meals['day'].mode()[0] if not user_meals['day'].mode().empty else None,
        'avg_price': (user_meals_details['price_min'].astype(float).mean() + user_meals_details['price_max'].astype(float).mean()) / 2,
        'top_tags': user_meals_details[['tag_1', 'tag_2', 'tag_3']].stack().mode().tolist()
    }
    return profile

def get_content_based_recs(user_profile, candidate_restaurants, all_seen_ids):
    """Generates content-based recommendations on a pre-filtered list of candidates."""
    if candidate_restaurants.empty: return []

    # Create a "document" for the user profile and each restaurant
    user_profile_doc = ' '.join(user_profile.get('top_tags', []))
    candidate_restaurants['tags_combined'] = candidate_restaurants[['tag_1', 'tag_2', 'tag_3']].fillna('').agg(' '.join, axis=1)
    
    # Combine user profile into the corpus for vectorization
    corpus = [user_profile_doc] + candidate_restaurants['tags_combined'].tolist()
    
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(corpus)
    
    # Calculate similarity between the user profile (first item) and all restaurants
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    
    sim_scores = sorted(list(enumerate(cosine_sim[0])), key=lambda x: x[1], reverse=True)
    
    recommended_ids = []
    for idx, score in sim_scores:
        restaurant_id = candidate_restaurants.iloc[idx]['id']
        if restaurant_id not in all_seen_ids:
            recommended_ids.append(restaurant_id)
        if len(recommended_ids) >= 15: break
    return recommended_ids

def get_svd_recs(user_id, reviews_df, candidate_restaurants, all_seen_ids):
    """Generates SVD recommendations on a pre-filtered list of candidates."""
    if reviews_df.empty or candidate_restaurants.empty: return []
    
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(reviews_df[['user_id', 'restaurant_id', 'rating']], reader)
    trainset = data.build_full_trainset()
    model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02)
    model.fit(trainset)
    
    # Predict ratings ONLY for the candidate restaurants
    candidate_ids = set(candidate_restaurants['id'])
    predictions = [model.predict(user_id, rest_id) for rest_id in candidate_ids]
    predictions.sort(key=lambda x: x.est, reverse=True)
    
    recommended_ids = []
    for pred in predictions:
        if pred.iid not in all_seen_ids:
            recommended_ids.append(pred.iid)
        if len(recommended_ids) >= 15: break
    return recommended_ids

# --- Main Hybrid "Warm Start" Model ---
def recommend_for_active_user(user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids=[]):
    print(f"Running Advanced Hybrid Model for user {user['id']}")
    _, current_meal_time = get_current_context()
    
    # 1. Build User Profile
    user_profile = build_user_profile(user['id'], meals_df, restaurants_df)
    
    # 2. Context-Aware Filtering
    # Prioritize restaurants that match the user's preferred mealtime, or the current time
    preferred_time = user_profile.get('top_meal_time', current_meal_time)
    
    # Find restaurants that are known to be visited during the preferred mealtime
    relevant_restaurant_ids = meals_df[meals_df['meal_time'] == preferred_time]['restaurant_id'].unique()
    candidate_restaurants = restaurants_df[restaurants_df['id'].isin(relevant_restaurant_ids)].copy()
    
    # Further filter by distance
    candidate_restaurants['distance'] = candidate_restaurants.apply(
        lambda row: haversine(user['latitude'], user['longitude'], row['latitude'], row['longitude']), axis=1
    )
    # Keep restaurants within a 20km radius
    candidate_restaurants = candidate_restaurants[candidate_restaurants['distance'] <= 20]

    if candidate_restaurants.empty:
        print("No candidates found after contextual filtering. Widening search.")
        candidate_restaurants = restaurants_df # Fallback to all restaurants

    # 3. Run Hybrid Models on Candidates
    eaten_restaurant_ids = interactions_df[(interactions_df['user_id'] == user['id']) & (interactions_df['user_action'] == 'eat')]['restaurant_id'].unique()
    all_seen_ids = set(eaten_restaurant_ids) | set(exclude_ids)

    cbf_recs = get_content_based_recs(user_profile, candidate_restaurants, all_seen_ids)
    svd_recs = get_svd_recs(user['id'], reviews_df, candidate_restaurants, all_seen_ids)

    # 4. Combine and Rank
    combined_recs = []
    max_len = max(len(cbf_recs), len(svd_recs))
    for i in range(max_len):
        if i < len(cbf_recs): combined_recs.append(cbf_recs[i])
        if i < len(svd_recs): combined_recs.append(svd_recs[i])
    
    unique_recs = list(dict.fromkeys(combined_recs))
    return unique_recs[:15]

# --- Main Orchestrator ---
def get_recommendations(user_id, exclude_ids=[]):
    users_df = pd.read_sql_table('user', engine); 
    reviews_df = pd.read_sql_table('review', engine); 
    restaurants_df = pd.read_sql_table('restaurant', engine); 
    interactions_df = pd.read_sql_table('interaction_log', engine)
    meals_df = pd.read_sql_table('meal', engine)
    
    try:
        current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
    except IndexError:
        return [] # User not found

    meal_count = get_meal_count(user_id, interactions_df)
    
    if meal_count < 15:
        return recommend_for_new_user(current_user, restaurants_df, meals_df, exclude_ids)
    else:
        return recommend_for_active_user(current_user, restaurants_df, interactions_df, reviews_df, meals_df, exclude_ids)
