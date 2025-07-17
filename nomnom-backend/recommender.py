import pandas as pd
from sqlalchemy import create_engine
from math import radians, sin, cos, sqrt, atan2
import os

# Get the database URL from environment variables, just like in app.py
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Use the production DB URL if available, otherwise fall back to local sqlite
engine = create_engine(db_url or 'sqlite:///nomnom.db')

# --- Helper Functions (No changes needed here) ---
def haversine(lat1, lon1, lat2, lon2):
    # ... (rest of the function is the same)
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# --- Recommendation Logic (No changes needed here) ---
def get_meal_count(user_id):
    """
    Check how many 'eat' interactions a user has logged in the
    InteractionLog table. This is a more reliable measure of activity.
    """
    query = f"SELECT COUNT(*) FROM interaction_log WHERE user_id = '{user_id}' AND user_action = 'eat'"
    with engine.connect() as connection:
        # .scalar() returns the first element of the first row, or None
        result = connection.execute(query).scalar()
    return result if result else 0

def recommend_for_new_user(target_user_id, all_users_df, reviews_df):
    # ... (rest of the function is the same)
    try:
        target_user = all_users_df[all_users_df['id'] == target_user_id].iloc[0]
    except IndexError:
        return []

    similarities = []
    for index, user in all_users_df.iterrows():
        if user['id'] == target_user_id:
            continue
        
        age_diff = abs(target_user['age'] - user['age'])
        age_score = max(0, 1 - (age_diff / 20)) 

        gender_score = 1 if target_user['gender'] == user['gender'] else 0.5
        
        distance = haversine(target_user['latitude'], target_user['longitude'], user['latitude'], user['longitude'])
        distance_score = max(0, 1 - (distance / 50))

        total_similarity = (age_score * 0.4) + (gender_score * 0.2) + (distance_score * 0.4)
        similarities.append((user['id'], total_similarity))

    similar_users = sorted(similarities, key=lambda x: x[1], reverse=True)[:10]
    similar_user_ids = [uid for uid, score in similar_users]

    recommendations = reviews_df[reviews_df['user_id'].isin(similar_user_ids)]
    top_rated_by_similar_users = recommendations[recommendations['rating'] >= 4]
    recommended_restaurants = top_rated_by_similar_users['restaurant_id'].value_counts().nlargest(10).index.tolist()

    return recommended_restaurants

def recommend_for_active_user(user_id):
    # ... (rest of the function is the same)
    query = "SELECT id FROM restaurant ORDER BY google_rating DESC LIMIT 10"
    with engine.connect() as connection:
        result = connection.execute(query)
        return [row[0] for row in result]

def get_recommendations(user_id):
    # ... (rest of the function is the same)
    users_df = pd.read_sql_table('user', engine)
    reviews_df = pd.read_sql_table('review', engine)
    
    meal_count = get_meal_count(user_id)
    
    if meal_count < 15:
        print(f"User {user_id} is a new user (meals: {meal_count}). Using cold-start model.")
        return recommend_for_new_user(user_id, users_df, reviews_df)
    else:
        print(f"User {user_id} is an active user (meals: {meal_count}). Using personalized model.")
        return recommend_for_active_user(user_id)