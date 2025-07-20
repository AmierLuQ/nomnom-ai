# =======================================================================
# NomNom AI: Offline Evaluation Script
# =======================================================================
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Import the core recommendation logic from your existing file
from recommender import recommend_for_active_user, get_meal_count

# --- Configuration ---
# The minimum number of meals a user must have to be included in the test
MINIMUM_MEALS_FOR_TESTING = 20 
# The number of recommendations to generate for each user
K = 15 

# =======================================================================
#  Metric Calculation Functions
# =======================================================================

def hit_rate_at_k(recommendations, test_set_ids):
    """
    Calculates the Hit Rate.
    Returns 1 if any recommended item is in the test set, otherwise 0.
    """
    for rec_id in recommendations:
        if rec_id in test_set_ids:
            return 1
    return 0

def precision_at_k(recommendations, test_set_ids):
    """
    Calculates Precision@K.
    Measures: What proportion of our recommendations were actually relevant?
    """
    hits = len(set(recommendations).intersection(test_set_ids))
    return hits / K

def recall_at_k(recommendations, test_set_ids):
    """
    Calculates Recall@K.
    Measures: What proportion of the relevant items did we successfully recommend?
    """
    hits = len(set(recommendations).intersection(test_set_ids))
    return hits / len(test_set_ids)

def average_precision_at_k(recommendations, test_set_ids):
    """
    Calculates Average Precision, which rewards correct rankings.
    A hit earlier in the list is scored higher than a hit later in the list.
    """
    hits = 0
    precision_scores = []
    for i, rec_id in enumerate(recommendations):
        if rec_id in test_set_ids:
            hits += 1
            precision_scores.append(hits / (i + 1))
    
    if not precision_scores:
        return 0.0
    
    return sum(precision_scores) / len(test_set_ids)

# =======================================================================
#  Main Evaluation Function
# =======================================================================

def evaluate_model():
    """
    Performs the full offline evaluation process.
    """
    print("--- Starting Offline Recommendation Model Evaluation ---")

    # --- 1. Load Data ---
    print("Connecting to database and loading data...")
    load_dotenv()
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not found in .env file.")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(db_url)
    
    users_df = pd.read_sql_table('user', engine)
    reviews_df = pd.read_sql_table('review', engine)
    restaurants_df = pd.read_sql_table('restaurant', engine)
    interactions_df = pd.read_sql_table('interaction_log', engine)
    meals_df = pd.read_sql_table('meal', engine)
    
    # Ensure date columns are in datetime format for sorting
    meals_df['date'] = pd.to_datetime(meals_df['date'])
    reviews_df['date'] = pd.to_datetime(reviews_df['date'])
    interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])

    print(f"Data loaded successfully: {len(users_df)} users, {len(meals_df)} meals.")

    # --- 2. Identify and Split Data for Test Users ---
    test_users = []
    for user_id in users_df['id']:
        user_meal_count = get_meal_count(user_id, interactions_df)
        if user_meal_count >= MINIMUM_MEALS_FOR_TESTING:
            test_users.append(user_id)
    
    if not test_users:
        print("\nNo users found with enough meal history for testing. Aborting.")
        return

    print(f"\nFound {len(test_users)} users with >= {MINIMUM_MEALS_FOR_TESTING} meals for testing.")

    all_metrics = []

    # --- 3. Run Evaluation Loop for Each User ---
    for user_id in test_users:
        print(f"\n--- Evaluating for User: {user_id} ---")
        
        # Chronological Split (80/20)
        user_meals = meals_df[meals_df['user_id'] == user_id].sort_values('date')
        split_point = int(len(user_meals) * 0.8)
        
        train_meals = user_meals.iloc[:split_point]
        test_meals = user_meals.iloc[split_point:]
        
        # The "ground truth" - what we are trying to predict
        test_set_ids = set(test_meals['restaurant_id'].unique())
        
        # Create training sets for all dataframes based on the meal dates
        max_train_date = train_meals['date'].max()
        train_reviews = reviews_df[(reviews_df['user_id'] == user_id) & (reviews_df['date'] <= max_train_date)]
        train_interactions = interactions_df[(interactions_df['user_id'] == user_id) & (interactions_df['timestamp'] <= max_train_date)]
        
        print(f"Split complete: {len(train_meals)} training meals, {len(test_meals)} testing meals.")

        # --- 4. Generate Recommendations using the Training Data ---
        try:
            # We need the full user object for the model
            current_user = users_df[users_df['id'] == user_id].iloc[0].to_dict()
            
            # Call the warm-start model directly with the training data subsets
            recommendations = recommend_for_active_user(
                user=current_user,
                restaurants_df=restaurants_df,
                interactions_df=train_interactions,
                reviews_df=train_reviews,
                meals_df=train_meals,
                exclude_ids=[] # Start with no exclusions
            )
            print(f"Generated {len(recommendations)} recommendations.")

            # --- 5. Calculate Metrics ---
            hit_rate = hit_rate_at_k(recommendations, test_set_ids)
            precision = precision_at_k(recommendations, test_set_ids)
            recall = recall_at_k(recommendations, test_set_ids)
            avg_precision = average_precision_at_k(recommendations, test_set_ids)
            
            all_metrics.append({
                'user_id': user_id,
                'hit_rate': hit_rate,
                'precision_at_k': precision,
                'recall_at_k': recall,
                'average_precision_at_k': avg_precision
            })
            print(f"Metrics: HitRate={hit_rate}, Precision@{K}={precision:.2f}, Recall@{K}={recall:.2f}, AP@{K}={avg_precision:.2f}")

        except Exception as e:
            print(f"An error occurred while evaluating user {user_id}: {e}")

    # --- 6. Aggregate and Display Final Results ---
    if not all_metrics:
        print("\nEvaluation could not be completed.")
        return

    results_df = pd.DataFrame(all_metrics)
    mean_hit_rate = results_df['hit_rate'].mean()
    mean_precision = results_df['precision_at_k'].mean()
    mean_recall = results_df['recall_at_k'].mean()
    mean_average_precision = results_df['average_precision_at_k'].mean() # This is MAP

    print("\n\n--- Overall Model Performance ---")
    print(f"Total Users Tested: {len(results_df)}")
    print(f"Hit Rate @ {K}: {mean_hit_rate:.2%}")
    print(f"Precision @ {K}: {mean_precision:.2%}")
    print(f"Recall @ {K}: {mean_recall:.2%}")
    print(f"Mean Average Precision (MAP) @ {K}: {mean_average_precision:.2%}")
    print("---------------------------------")


if __name__ == '__main__':
    evaluate_model()
