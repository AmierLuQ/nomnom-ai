import pandas as pd
from sqlalchemy import create_engine
from math import radians, sin, cos, sqrt, atan2

# --- Database Connection ---
# Use the same database file as your Flask app
db_uri = 'sqlite:///nomnom.db'
engine = create_engine(db_uri)

# --- Helper Functions ---
def haversine(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on Earth."""
    R = 6371  # Radius of Earth in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance

# --- Recommendation Logic ---

def get_meal_count(user_id):
    """Check how many meals a user has logged."""
    query = f"SELECT COUNT(*) FROM meal WHERE user_id = '{user_id}'"
    with engine.connect() as connection:
        result = connection.execute(query).scalar()
    return result if result else 0

def recommend_for_new_user(target_user_id, all_users_df, reviews_df):
    """
    Recommend for new users based on demographic similarity (age, gender, location).
    This is a user-based collaborative filtering approach using demographics.
    """
    try:
        target_user = all_users_df[all_users_df['id'] == target_user_id].iloc[0]
    except IndexError:
        return [] # User not found

    similarities = []
    for index, user in all_users_df.iterrows():
        if user['id'] == target_user_id:
            continue

        # Calculate similarity score
        age_diff = abs(target_user['age'] - user['age'])
        age_score = max(0, 1 - (age_diff / 20)) # Normalize age difference

        gender_score = 1 if target_user['gender'] == user['gender'] else 0.5
        
        distance = haversine(target_user['latitude'], target_user['longitude'], user['latitude'], user['longitude'])
        distance_score = max(0, 1 - (distance / 50)) # Normalize distance (assuming 50km is a max relevant distance)

        # Weighted similarity score
        total_similarity = (age_score * 0.4) + (gender_score * 0.2) + (distance_score * 0.4)
        similarities.append((user['id'], total_similarity))

    # Get top 10 similar users
    similar_users = sorted(similarities, key=lambda x: x[1], reverse=True)[:10]
    similar_user_ids = [uid for uid, score in similar_users]

    # Get restaurants highly rated by these similar users
    recommendations = reviews_df[reviews_df['user_id'].isin(similar_user_ids)]
    
    # Filter for high ratings and sort
    top_rated_by_similar_users = recommendations[recommendations['rating'] >= 4]
    
    # Count occurrences and get top recommendations
    recommended_restaurants = top_rated_by_similar_users['restaurant_id'].value_counts().nlargest(10).index.tolist()

    return recommended_restaurants

def recommend_for_active_user(user_id):
    """Placeholder for personalized recommendations for active users."""
    # We will build this in the next step.
    # For now, let's return a simple placeholder.
    query = "SELECT id FROM restaurant ORDER BY google_rating DESC LIMIT 10"
    with engine.connect() as connection:
        result = connection.execute(query)
        return [row[0] for row in result]


def get_recommendations(user_id):
    """Main recommendation function."""
    # Load data from DB into DataFrames
    users_df = pd.read_sql_table('user', engine)
    reviews_df = pd.read_sql_table('review', engine)
    
    # Check user meal count to decide strategy
    meal_count = get_meal_count(user_id)
    
    if meal_count < 15:
        print(f"User {user_id} is a new user (meals: {meal_count}). Using cold-start model.")
        return recommend_for_new_user(user_id, users_df, reviews_df)
    else:
        print(f"User {user_id} is an active user (meals: {meal_count}). Using personalized model.")
        return recommend_for_active_user(user_id)