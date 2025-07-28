# =======================================================================
# NomNom AI: Offline Evaluation Script (with Detailed Metrics)
# =======================================================================

# --- Path Correction ---
# This block allows the script to be run from the 'scripts' folder and still
# find the main application modules (like 'recommender').
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---------------------

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import warnings
import numpy as np

# Import the core recommendation logic from your existing file
from recommender import recommend_for_active_user, get_meal_count, haversine

# Suppress UserWarning from sklearn about feature names
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

# --- Configuration ---
MINIMUM_MEALS_FOR_TESTING = 20
K = 10 # Using @10 for all metrics

# Maps a mealtime name to a representative float hour
MEAL_TIME_TO_HOUR_MAP = {
    "Suhoor": 5.5, "Breakfast": 8.5, "Brunch": 11.0, "Lunch": 14.0,
    "Tea Time": 16.75, "Linner": 18.5, "Dinner": 20.75, "Late Dinner": 22.75,
    "Midnight Snack": 0.75,
}

# =======================================================================
#  Metric Calculation Functions
# =======================================================================
def calculate_all_metrics(recommendations, ground_truth_ids, k):
    """Calculates and prints all metrics for a single prediction."""
    
    is_hit = 1 if any(rec in ground_truth_ids for rec in recommendations) else 0
    print(f"     - Hit Rate @{k}:")
    print(f"       Formula: 1 if (Recommended ∩ GroundTruth) > 0 else 0")
    print(f"       Calculation: {'1 (Hit!)' if is_hit else '0 (Miss)'}")

    hits = len(set(recommendations).intersection(ground_truth_ids))
    precision = hits / k if k > 0 else 0
    print(f"     - Precision @{k}:")
    print(f"       Formula: |Recommended ∩ GroundTruth| / k")
    print(f"       Calculation: {hits} / {k} = {precision:.4f}")

    recall = hits / len(ground_truth_ids) if ground_truth_ids else 0
    print(f"     - Recall @{k}:")
    print(f"       Formula: |Recommended ∩ GroundTruth| / |GroundTruth|")
    print(f"       Calculation: {hits} / {len(ground_truth_ids)} = {recall:.4f}")

    ap_hits = 0; ap_sum = 0; ap_steps = []
    for i, rec_id in enumerate(recommendations):
        if rec_id in ground_truth_ids:
            ap_hits += 1
            precision_at_i = ap_hits / (i + 1)
            ap_sum += precision_at_i
            ap_steps.append(f"(Hit {ap_hits} at pos {i+1} -> Precision={precision_at_i:.2f})")
    
    ap = ap_sum / len(ground_truth_ids) if ground_truth_ids else 0
    print(f"     - Average Precision @{k}:")
    print(f"       Formula: (Σ [Precision of each hit]) / |GroundTruth|")
    if ap_steps: print(f"       Steps: {', '.join(ap_steps)}")
    print(f"       Calculation: {ap_sum:.2f} / {len(ground_truth_ids)} = {ap:.4f}")

    relevance = [1 if rec in ground_truth_ids else 0 for rec in recommendations]
    ideal_relevance = sorted(relevance, reverse=True)
    dcg = sum([rel / np.log2(i + 2) for i, rel in enumerate(relevance)])
    idcg = sum([rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevance)])
    ndcg = dcg / idcg if idcg > 0 else 0
    print(f"     - nDCG @{k}:")
    print(f"       Formula: DCG / IDCG")
    print(f"       Calculation: {dcg:.2f} / {idcg:.2f} = {ndcg:.4f}")
    
    return {'hit_rate': is_hit, 'precision_at_k': precision, 'recall_at_k': recall, 'average_precision_at_k': ap, 'ndcg_at_k': ndcg}

# =======================================================================
#  Main Evaluation Function
# =======================================================================
def evaluate_model():
    print("--- Starting Offline Recommendation Model Evaluation ---")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
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

    if not meals_df.empty:
        user_locs = users_df.set_index('id')[['latitude', 'longitude']].to_dict('index')
        rest_locs = restaurants_df.set_index('id')[['latitude', 'longitude']].to_dict('index')
        meals_df['user_lat'] = meals_df['user_id'].map(lambda x: user_locs.get(x, {}).get('latitude'))
        meals_df['user_lon'] = meals_df['user_id'].map(lambda x: user_locs.get(x, {}).get('longitude'))
        meals_df['rest_lat'] = meals_df['restaurant_id'].map(lambda x: rest_locs.get(x, {}).get('latitude'))
        meals_df['rest_lon'] = meals_df['restaurant_id'].map(lambda x: rest_locs.get(x, {}).get('longitude'))
        meals_df['distance_travelled'] = meals_df.apply(lambda r: haversine(r['user_lat'], r['user_lon'], r['rest_lat'], r['rest_lon']), axis=1)
        meals_df.drop(columns=['user_lat', 'user_lon', 'rest_lat', 'rest_lon'], inplace=True)
        print("Distance travelled for all meals calculated.")

    test_users = [uid for uid in users_df['id'] if get_meal_count(uid, meals_df) >= MINIMUM_MEALS_FOR_TESTING]
    if not test_users:
        print("\nNo users found with enough meal history for testing. Aborting.")
        return

    print(f"\nFound {len(test_users)} users for testing.")
    all_user_metrics = []
    debug_results = []
    
    restaurant_name_map = restaurants_df.set_index('id')['name'].to_dict()

    for user_id in test_users:
        print(f"\n{'='*25}\n--- Evaluating for User: {user_id} ---\n{'='*25}")
        user_meals = meals_df[meals_df['user_id'] == user_id].sort_values('date')
        split_point = int(len(user_meals) * 0.8)
        train_meals = user_meals.iloc[:split_point]
        test_meals = user_meals.iloc[split_point:]
        
        max_train_date = train_meals['date'].max()
        train_reviews = reviews_df[(reviews_df['user_id'] == user_id) & (reviews_df['date'] <= max_train_date)]
        
        train_interactions = pd.DataFrame(columns=['id', 'user_id', 'restaurant_id', 'user_action', 'timestamp'])
        
        current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
        user_predictions_metrics = []
        
        test_set_names = [restaurant_name_map.get(rid, rid) for rid in test_meals['restaurant_id'].unique()]
        print(f"Training with {len(train_meals)} meals. Testing against {len(test_meals)} future meals.")
        print(f"Future meals (Ground Truth): {', '.join(test_set_names)}")
        
        for i, (_, test_meal) in enumerate(test_meals.iterrows()):
            print(f"\n  Test #{i+1}: Predicting for meal on {test_meal['date'].date()} ({test_meal['day']} {test_meal['meal_time']})")
            ground_truth_id = test_meal['restaurant_id']
            ground_truth_name = restaurant_name_map.get(ground_truth_id, "Unknown")
            print(f"  Real Outcome: User went to '{ground_truth_name}' ({ground_truth_id})")

            simulated_context = (test_meal['day'], test_meal['meal_time'], MEAL_TIME_TO_HOUR_MAP.get(test_meal['meal_time'], 14.0))
            
            recommendations = recommend_for_active_user(
                user=current_user, restaurants_df=restaurants_df,
                interactions_df=train_interactions, reviews_df=train_reviews,
                meals_df=train_meals, exclude_ids=[], context=simulated_context
            )[:K]
            
            rec_names = [restaurant_name_map.get(rid, rid) for rid in recommendations]
            print(f"  Top {K} Recommendations: {', '.join(rec_names)}")
            
            metrics = calculate_all_metrics(recommendations, {ground_truth_id}, K)
            user_predictions_metrics.append(metrics)

            debug_results.append({
                'user_id': user_id, 'simulated_day': test_meal['day'], 'simulated_meal_time': test_meal['meal_time'],
                'ground_truth_id': ground_truth_id, 'ground_truth_name': ground_truth_name,
                'recommendation_1': restaurant_name_map.get(recommendations[0], None) if len(recommendations) > 0 else None,
                'recommendation_2': restaurant_name_map.get(recommendations[1], None) if len(recommendations) > 1 else None,
                'recommendation_3': restaurant_name_map.get(recommendations[2], None) if len(recommendations) > 2 else None,
                'full_recommendation_ids': recommendations,
                'hit': metrics['hit_rate']
            })

        if not user_predictions_metrics: continue
        
        user_metrics_df = pd.DataFrame(user_predictions_metrics)
        avg_user_metrics = user_metrics_df.mean().to_dict()
        all_user_metrics.append(avg_user_metrics)
        print(f"\n   --- User {user_id} Summary ---")
        print(f"   Avg Hit Rate: {avg_user_metrics['hit_rate']:.2%}, Avg Precision: {avg_user_metrics['precision_at_k']:.2%}, Avg Recall: {avg_user_metrics['recall_at_k']:.2%}, MAP: {avg_user_metrics['average_precision_at_k']:.2%}, Avg nDCG: {avg_user_metrics['ndcg_at_k']:.2%}")

    if not all_user_metrics:
        print("\nEvaluation could not be completed.")
        return

    # Define the output path for the debug file inside the 'scripts' directory
    output_path = os.path.join(os.path.dirname(__file__), 'evaluation_results.csv')
    debug_df = pd.DataFrame(debug_results)
    debug_df.to_csv(output_path, index=False)
    print(f"\n\nDetailed debug file '{output_path}' has been generated.")

    results_df = pd.DataFrame(all_user_metrics)
    final_metrics = results_df.mean()

    print("\n\n--- Overall Model Performance ---")
    print(f"Total Users Tested: {len(results_df)}")
    print(f"Hit Rate @ {K}: {final_metrics['hit_rate']:.2%}")
    print(f"Precision @ {K}: {final_metrics['precision_at_k']:.2%}")
    print(f"Recall @ {K}: {final_metrics['recall_at_k']:.2%}")
    print(f"Mean Average Precision (MAP) @ {K}: {final_metrics['average_precision_at_k']:.2%}")
    print(f"Normalized Discounted Cumulative Gain (nDCG) @ {K}: {final_metrics['ndcg_at_k']:.2%}")
    print("---------------------------------")

if __name__ == '__main__':
    evaluate_model()
