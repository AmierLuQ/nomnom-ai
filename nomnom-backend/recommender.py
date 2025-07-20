# =======================================================================
# NomNom AI: Offline Evaluation Script (with Time Simulation)
# =======================================================================
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Import the core recommendation logic from your existing file
from recommender import recommend_for_active_user, get_meal_count, is_restaurant_open

# --- Configuration ---
MINIMUM_MEALS_FOR_TESTING = 20 
K = 15 

# --- NEW: Time Simulation Mapping ---
# Maps a mealtime name to a representative float hour (mid-point of the range)
MEAL_TIME_TO_HOUR_MAP = {
    "Suhoor": 5.5,          # 4:00 AM - 7:00 AM
    "Breakfast": 8.5,       # 7:00 AM - 10:00 AM
    "Brunch": 11.0,         # 10:00 AM - 12:00 PM
    "Lunch": 14.0,          # 12:00 PM - 4:00 PM
    "Tea Time": 16.75,      # 4:00 PM - 5:30 PM
    "Linner": 18.5,         # 5:30 PM - 7:30 PM
    "Dinner": 20.75,        # 7:30 PM - 10:00 PM
    "Late Dinner": 22.75,   # 10:00 PM - 11:30 PM
    "Midnight Snack": 0.75, # 11:30 PM - 2:00 AM (represented as 00:45)
}

# =======================================================================
#  Metric Calculation Functions
# =======================================================================

def hit_rate_at_k(recommendations, test_set_ids):
    """Calculates the Hit Rate."""
    return 1 if any(rec_id in test_set_ids for rec_id in recommendations) else 0

def precision_at_k(recommendations, test_set_ids):
    """Calculates Precision@K."""
    hits = len(set(recommendations).intersection(test_set_ids))
    return hits / K

def recall_at_k(recommendations, test_set_ids):
    """Calculates Recall@K."""
    hits = len(set(recommendations).intersection(test_set_ids))
    return hits / len(test_set_ids)

def average_precision_at_k(recommendations, test_set_ids):
    """Calculates Average Precision, rewarding correct rankings."""
    hits = 0
    precision_scores = []
    for i, rec_id in enumerate(recommendations):
        if rec_id in test_set_ids:
            hits += 1
            precision_scores.append(hits / (i + 1))
    
    if not precision_scores: return 0.0
    return sum(precision_scores) / len(test_set_ids)

# =======================================================================
#  Main Evaluation Function
# =======================================================================

def evaluate_model():
    """Performs the full offline evaluation process with time simulation."""
    print("--- Starting Offline Recommendation Model Evaluation ---")

    # --- 1. Load Data ---
    print("Connecting to database and loading data...")
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    if not db_url: raise ValueError("DATABASE_URL not found in .env file.")
    if db_url.startswith("postgres://"): db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(db_url)
    users_df = pd.read_sql_table('user', engine)
    reviews_df = pd.read_sql_table('review', engine)
    restaurants_df = pd.read_sql_table('restaurant', engine)
    interactions_df = pd.read_sql_table('interaction_log', engine)
    meals_df = pd.read_sql_table('meal', engine)
    
    meals_df['date'] = pd.to_datetime(meals_df['date'])
    reviews_df['date'] = pd.to_datetime(reviews_df['date'])
    interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])
    print(f"Data loaded successfully: {len(users_df)} users, {len(meals_df)} meals.")

    # --- 2. Identify and Split Data for Test Users ---
    test_users = [uid for uid in users_df['id'] if get_meal_count(uid, interactions_df) >= MINIMUM_MEALS_FOR_TESTING]
    if not test_users:
        print("\nNo users found with enough meal history for testing. Aborting.")
        return
    print(f"\nFound {len(test_users)} users with >= {MINIMUM_MEALS_FOR_TESTING} meals for testing.")

    all_user_metrics = []

    # --- 3. Run Evaluation Loop for Each User ---
    for user_id in test_users:
        print(f"\n--- Evaluating for User: {user_id} ---")
        
        user_meals = meals_df[meals_df['user_id'] == user_id].sort_values('date')
        split_point = int(len(user_meals) * 0.8)
        train_meals = user_meals.iloc[:split_point]
        test_meals = user_meals.iloc[split_point:]
        
        max_train_date = train_meals['date'].max()
        train_reviews = reviews_df[(reviews_df['user_id'] == user_id) & (reviews_df['date'] <= max_train_date)]
        train_interactions = interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['timestamp'] <= max_train_date)]
        
        current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
        
        user_predictions = []
        
        # --- 4. NEW: Loop through each future meal to simulate the context ---
        for _, test_meal in test_meals.iterrows():
            ground_truth_id = test_meal['restaurant_id']
            simulated_day = test_meal['day']
            simulated_meal_time = test_meal['meal_time']
            simulated_time_float = MEAL_TIME_TO_HOUR_MAP.get(simulated_meal_time, 14.0) # Default to Lunch if not found
            
            # This is the context at the time of the meal
            simulated_context = (simulated_day, simulated_meal_time, simulated_time_float)
            
            # Generate recommendations using the training data and SIMULATED context
            # We need to modify the recommender call to accept the simulated context
            # For now, we will manually filter the results as a proof of concept
            
            recommendations = recommend_for_active_user(
                user=current_user,
                restaurants_df=restaurants_df,
                interactions_df=train_interactions,
                reviews_df=train_reviews,
                meals_df=train_meals,
                exclude_ids=[] 
            )
            
            # Manually filter the recommendations to only include open restaurants at the simulated time
            rec_details = restaurants_df[restaurants_df['id'].isin(recommendations)]
            open_recs_details = rec_details[rec_details.apply(is_restaurant_open, args=(simulated_time_float,), axis=1)]
            
            # Re-order based on original recommendation list and take top K
            open_recs_ordered = [rec for rec in recommendations if rec in open_recs_details['id'].tolist()]
            final_recommendations = open_recs_ordered[:K]

            user_predictions.append({
                'recommendations': final_recommendations,
                'ground_truth': {ground_truth_id} # Use a set for efficient lookup
            })

        # --- 5. Calculate Metrics for this user ---
        if not user_predictions: continue
            
        user_hit_rate = sum(hit_rate_at_k(p['recommendations'], p['ground_truth']) for p in user_predictions) / len(user_predictions)
        user_precision = sum(precision_at_k(p['recommendations'], p['ground_truth']) for p in user_predictions) / len(user_predictions)
        user_recall = sum(recall_at_k(p['recommendations'], p['ground_truth']) for p in user_predictions) / len(user_predictions)
        user_ap = sum(average_precision_at_k(p['recommendations'], p['ground_truth']) for p in user_predictions) / len(user_predictions)
        
        all_user_metrics.append({
            'user_id': user_id, 'hit_rate': user_hit_rate, 'precision_at_k': user_precision,
            'recall_at_k': user_recall, 'average_precision_at_k': user_ap
        })
        print(f"User Metrics: HitRate={user_hit_rate:.2f}, Precision@{K}={user_precision:.2f}, Recall@{K}={user_recall:.2f}, AP@{K}={user_ap:.2f}")

    # --- 6. Aggregate and Display Final Results ---
    if not all_user_metrics:
        print("\nEvaluation could not be completed.")
        return

    results_df = pd.DataFrame(all_user_metrics)
    mean_hit_rate = results_df['hit_rate'].mean()
    mean_precision = results_df['precision_at_k'].mean()
    mean_recall = results_df['recall_at_k'].mean()
    mean_average_precision = results_df['average_precision_at_k'].mean()

    print("\n\n--- Overall Model Performance ---")
    print(f"Total Users Tested: {len(results_df)}")
    print(f"Hit Rate @ {K}: {mean_hit_rate:.2%}")
    print(f"Precision @ {K}: {mean_precision:.2%}")
    print(f"Recall @ {K}: {mean_recall:.2%}")
    print(f"Mean Average Precision (MAP) @ {K}: {mean_average_precision:.2%}")
    print("---------------------------------")

if __name__ == '__main__':
    evaluate_model()
