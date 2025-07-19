import pandas as pd
from sqlalchemy import create_engine, text
from math import radians, sin, cos, sqrt, atan2, log
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- Database Connection ---
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
engine = create_engine(db_url or 'sqlite:///nomnom.db')

# --- Helper Functions ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# --- Recommendation Logic ---
def get_meal_count(user_id):
    query_string = f"SELECT COUNT(*) FROM interaction_log WHERE user_id = '{user_id}' AND user_action = 'eat'"
    with engine.connect() as connection:
        result = connection.execute(text(query_string)).scalar()
    return result if result else 0

# --- MODIFIED FUNCTION ---
def recommend_for_new_user(target_user_id, all_users_df, reviews_df, restaurants_df, exclude_ids=[]):
    """
    Recommend for new users based on demographic similarity.
    If no similar user recommendations are found, fall back to globally popular restaurants.
    """
    try:
        target_user = all_users_df[all_users_df['id'] == target_user_id].iloc[0]
    except IndexError:
        return []

    # --- Part 1: Try to find recommendations from similar users ---
    similarities = []
    for index, user in all_users_df.iterrows():
        if user['id'] == target_user_id: continue
        age_diff = abs(target_user['age'] - user['age'])
        age_score = max(0, 1 - (age_diff / 20))
        gender_score = 1 if target_user['gender'] == user['gender'] else 0.5
        distance = haversine(target_user['latitude'], target_user['longitude'], user['latitude'], user['longitude'])
        distance_score = max(0, 1 - (distance / 50))
        total_similarity = (age_score * 0.4) + (gender_score * 0.2) + (distance_score * 0.4)
        similarities.append((user['id'], total_similarity))

    similar_users = sorted(similarities, key=lambda x: x[1], reverse=True)[:10]
    similar_user_ids = [uid for uid, score in similar_users]
    
    recommended_restaurants = []
    if similar_user_ids:
        recommendations = reviews_df[reviews_df['user_id'].isin(similar_user_ids)]
        # FIX: Lowered rating threshold from 4 to 3 to be less strict
        top_rated_by_similar_users = recommendations[recommendations['rating'] >= 3]
        all_recs = top_rated_by_similar_users['restaurant_id'].value_counts().index.tolist()
        recommended_restaurants = [rec for rec in all_recs if rec not in exclude_ids]

    # --- Part 2: Fallback to globally popular if no recommendations were found ---
    if not recommended_restaurants:
        print("No similar user recommendations found. Falling back to global popularity.")
        # Calculate a popularity score: rating * log(reviews). This balances quality and popularity.
        # We add 1 to num_google_reviews to avoid log(0).
        restaurants_df['popularity_score'] = restaurants_df['google_rating'] * restaurants_df['num_google_reviews'].apply(lambda x: log(x + 1))
        
        # Sort by the new score and get the top restaurant IDs
        popular_recs = restaurants_df.sort_values('popularity_score', ascending=False)
        all_popular_ids = popular_recs['id'].tolist()
        
        # Filter out any already excluded IDs
        recommended_restaurants = [rec for rec in all_popular_ids if rec not in exclude_ids]

    return recommended_restaurants[:10] # Return the top 10 from whichever method worked


def recommend_for_active_user(user_id, restaurants_df, interactions_df, exclude_ids=[]):
    user_eaten_restaurants = interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['user_action'] == 'eat')]
    eaten_restaurant_ids = user_eaten_restaurants['restaurant_id'].unique()
    if len(eaten_restaurant_ids) == 0: return []

    restaurants_df['tags_combined'] = restaurants_df[['tag_1', 'tag_2', 'tag_3']].fillna('').agg(' '.join, axis=1)
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(restaurants_df['tags_combined'])
    user_profile_indices = restaurants_df[restaurants_df['id'].isin(eaten_restaurant_ids)].index
    user_profile_vector = tfidf_matrix[user_profile_indices].mean(axis=0)
    cosine_sim = cosine_similarity(user_profile_vector, tfidf_matrix)
    sim_scores = list(enumerate(cosine_sim[0]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    all_seen_ids = set(eaten_restaurant_ids) | set(exclude_ids)
    
    recommended_ids = []
    for idx, score in sim_scores:
        restaurant_id = restaurants_df.iloc[idx]['id']
        if restaurant_id not in all_seen_ids:
            recommended_ids.append(restaurant_id)
        if len(recommended_ids) >= 10:
            break
            
    return recommended_ids

# --- MODIFIED FUNCTION ---
def get_recommendations(user_id, exclude_ids=[]):
    """Main recommendation function, now passes restaurants_df to the new user model."""
    users_df = pd.read_sql_table('user', engine)
    reviews_df = pd.read_sql_table('review', engine)
    restaurants_df = pd.read_sql_table('restaurant', engine)
    interactions_df = pd.read_sql_table('interaction_log', engine)
    
    meal_count = get_meal_count(user_id)
    
    if meal_count < 15:
        print(f"User {user_id} is a new user. Using cold-start model.")
        # FIX: Pass the restaurants_df for the new fallback logic
        return recommend_for_new_user(user_id, users_df, reviews_df, restaurants_df, exclude_ids)
    else:
        print(f"User {user_id} is an active user. Using personalized model.")
        return recommend_for_active_user(user_id, restaurants_df, interactions_df, exclude_ids)

