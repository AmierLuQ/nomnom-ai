# =======================================================================
# NomNom AI: Offline Evaluation Script (with Time Simulation & Debug Output)
# =======================================================================
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import warnings

# Import the core recommendation logic from your existing file
from recommender import recommend_for_active_user, get_meal_count

# Suppress UserWarning from sklearn about feature names
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

# --- Configuration ---
MINIMUM_MEALS_FOR_TESTING = 20 
K = 15 

# Maps a mealtime name to a representative float hour
MEAL_TIME_TO_HOUR_MAP = {
    "Suhoor": 5.5, "Breakfast": 8.5, "Brunch": 11.0, "Lunch": 14.0,
    "Tea Time": 16.75, "Linner": 18.5, "Dinner": 20.75, "Late Dinner": 22.75,
    "Midnight Snack": 0.75,
}

# =======================================================================
#  Metric Calculation Functions
# =======================================================================
def hit_rate_at_k(recommendations, test_set_ids):
    return 1 if any(rec_id in test_set_ids for rec_id in recommendations) else 0

def precision_at_k(recommendations, test_set_ids):
    hits = len(set(recommendations).intersection(test_set_ids))
    return hits / K if K > 0 else 0

def recall_at_k(recommendations, test_set_ids):
    hits = len(set(recommendations).intersection(test_set_ids))
    return hits / len(test_set_ids) if test_set_ids else 0

def average_precision_at_k(recommendations, test_set_ids):
    hits = 0; precision_scores = []
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
    print("--- Starting Offline Recommendation Model Evaluation ---")
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    if not db_url: raise ValueError("DATABASE_URL not found in .env file.")
    if db_url.startswith("postgres://"): db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(db_url)
    users_df = pd.read_sql_table('user', engine)
    reviews_df = pd.read_sql_table('review', engine)
    restaurants_df = pd.read_sql_table('restaurant', engine)
    meals_df = pd.read_sql_table('meal', engine)
    
    meals_df['date'] = pd.to_datetime(meals_df['date'])
    reviews_df['date'] = pd.to_datetime(reviews_df['date'])
    
    print(f"Data loaded: {len(users_df)} users, {len(meals_df)} meals.")

    test_users = [uid for uid in users_df['id'] if get_meal_count(uid, meals_df) >= MINIMUM_MEALS_FOR_TESTING]
    if not test_users:
        print("\nNo users found with enough meal history for testing. Aborting.")
        return

    print(f"\nFound {len(test_users)} users for testing.")
    all_user_metrics = []
    debug_results = []

    for user_id in test_users:
        print(f"\n--- Evaluating for User: {user_id} ---")
        user_meals = meals_df[meals_df['user_id'] == user_id].sort_values('date')
        split_point = int(len(user_meals) * 0.8)
        train_meals = user_meals.iloc[:split_point]
        test_meals = user_meals.iloc[split_point:]
        
        max_train_date = train_meals['date'].max()
        train_reviews = reviews_df[(reviews_df['user_id'] == user_id) & (reviews_df['date'] <= max_train_date)]
        
        # For evaluation, we don't have live interactions, so we pass an empty DataFrame
        train_interactions = pd.DataFrame() 
        
        current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
        user_predictions = []
        
        for _, test_meal in test_meals.iterrows():
            ground_truth_id = test_meal['restaurant_id']
            
            # --- FIX: Create the simulated context to pass to the model ---
            simulated_context = (
                test_meal['day'], 
                test_meal['meal_time'], 
                MEAL_TIME_TO_HOUR_MAP.get(test_meal['meal_time'], 14.0) # Default to Lunch if not found
            )
            
            recommendations = recommend_for_active_user(
                user=current_user, restaurants_df=restaurants_df,
                interactions_df=train_interactions, reviews_df=train_reviews,
                meals_df=train_meals, exclude_ids=[], 
                context=simulated_context # Pass the simulated context here
            )
            
            hits = set(recommendations).intersection({ground_truth_id})
            
            debug_results.append({
                'user_id': user_id,
                'simulated_day': test_meal['day'],
                'simulated_meal_time': test_meal['meal_time'],
                'ground_truth': ground_truth_id,
                'recommendations': recommendations,
                'hit': 1 if hits else 0
            })
            
            user_predictions.append({'recommendations': recommendations, 'ground_truth': {ground_truth_id}})

        if not user_predictions: continue
        user_hit_rate = sum(hit_rate_at_k(p['recommendations'], p['ground_truth']) for p in user_predictions) / len(user_predictions)
        user_precision = sum(precision_at_k(p['recommendations'], p['ground_truth']) for p in user_predictions) / len(user_predictions)
        user_recall = sum(recall_at_k(p['recommendations'], p['ground_truth']) for p in user_predictions) / len(user_predictions)
        user_ap = sum(average_precision_at_k(p['recommendations'], p['ground_truth']) for p in user_predictions) / len(user_predictions)
        all_user_metrics.append({'user_id': user_id, 'hit_rate': user_hit_rate, 'precision_at_k': user_precision, 'recall_at_k': user_recall, 'average_precision_at_k': user_ap})
        print(f"User Metrics: HitRate={user_hit_rate:.2f}, Precision@{K}={user_precision:.2f}, Recall@{K}={user_recall:.2f}, AP@{K}={user_ap:.2f}")

    if not all_user_metrics:
        print("\nEvaluation could not be completed.")
        return

    # --- Generate Debug Output File ---
    debug_df = pd.DataFrame(debug_results)
    debug_df.to_csv('evaluation_results.csv', index=False)
    print("\n\nDetailed debug file 'evaluation_results.csv' has been generated.")

    # --- Aggregate and Display Final Results ---
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
