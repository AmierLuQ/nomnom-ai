# =======================================================================
# NomNom AI: Database Seeder
# This script should be run from the `scripts` directory.
# =======================================================================

# --- Path Correction ---
# Allows the script to find the main 'app' module from the parent directory
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---------------------

import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import numpy as np

# --- Application Imports (for factory pattern) ---
from app import create_app, db, bcrypt
from app.models import User, Restaurant, Meal, Review, InteractionLog

# Create a Flask app instance to work with the database
app = create_app()

def seed_data():
    """
    Drops all existing data, recreates tables, and populates them
    from CSV files in a single database transaction.
    """
    print("Starting the seeding process...")

    # --- Load Environment Variables ---
    # Looks for the .env file in the parent directory (project root)
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    db_url_from_env = os.environ.get('DATABASE_URL')
    print(f"\n[DEBUG] Connecting to database specified in .env file:")
    print(f"[DEBUG] {db_url_from_env}\n")
    
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Tables created successfully.")

        try:
            # --- Define base path for data files ---
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data')

            # --- 1. Prepare Users ---
            print("\nPreparing users...")
            users_df = pd.read_csv(os.path.join(data_path, 'users.csv'))
            for _, row in users_df.iterrows():
                hashed_pw = bcrypt.generate_password_hash(row['password']).decode('utf-8')
                
                dob = None
                if pd.notna(row['dob']):
                    try:
                        dob = datetime.strptime(str(row['dob']), '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse date '{row['dob']}' for user {row['id']}.")
                user = User(id=row['id'], username=row['username'].lower(), name=row['name'], email=row['email'].lower(), phone=row.get('phone'), dob=dob, age=int(row['age']) if pd.notna(row['age']) else None, gender=row['gender'], latitude=row['latitude'], longitude=row['longitude'], password=hashed_pw)
                db.session.add(user)
            print(f"-> {len(users_df)} users ready.")

            # --- 2. Prepare Restaurants ---
            print("\nPreparing restaurants...")
            restaurants_df = pd.read_csv(os.path.join(data_path, 'restaurants.csv')).replace({np.nan: None})
            for _, row in restaurants_df.iterrows():
                restaurant = Restaurant(**row.to_dict())
                db.session.add(restaurant)
            print(f"-> {len(restaurants_df)} restaurants ready.")

            # --- 3. Prepare Meals ---
            print("\nPreparing meals...")
            meals_df = pd.read_csv(os.path.join(data_path, 'meals.csv')).replace({np.nan: None})
            for _, row in meals_df.iterrows():
                meal_date = None
                if pd.notna(row['date']):
                    try:
                        meal_date = datetime.strptime(str(row['date']), '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse date '{row['date']}' for meal {row['id']}.")
                meal = Meal(id=row['id'], user_id=row['user_id'], restaurant_id=row['restaurant_id'], date=meal_date, day=row['day'], meal_time=row['meal_time'])
                db.session.add(meal)
            print(f"-> {len(meals_df)} meals ready.")

            # --- 4. Prepare Reviews ---
            print("\nPreparing reviews...")
            reviews_df = pd.read_csv(os.path.join(data_path, 'reviews.csv')).replace({np.nan: None})
            for _, row in reviews_df.iterrows():
                review_date = None
                if pd.notna(row['date']):
                    try:
                        review_date = datetime.strptime(str(row['date']), '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse date '{row['date']}' for review {row['id']}.")
                review = Review(id=row['id'], user_id=row['user_id'], restaurant_id=row['restaurant_id'], date=review_date, rating=int(row['rating']), price_satisfaction=bool(row['price_satisfaction']) if pd.notna(row['price_satisfaction']) else None, visit_frequency=int(row['visit_frequency']) if pd.notna(row['visit_frequency']) else None)
                db.session.add(review)
            print(f"-> {len(reviews_df)} reviews ready.")

            # --- 5. Prepare Interaction Logs ---
            print("\nPreparing interaction logs...")
            interactions_df = pd.read_csv(os.path.join(data_path, 'interaction_logs.csv')).replace({np.nan: None})
            for _, row in interactions_df.iterrows():
                timestamp = None
                if pd.notna(row['timestamp']):
                    try:
                        timestamp = datetime.strptime(str(row['timestamp']), '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse timestamp '{row['timestamp']}' for log {row['id']}.")
                
                final_ordered = None
                if pd.notna(row['final_ordered']):
                    val = str(row['final_ordered']).lower()
                    if val in ['true', '1', 't', 'y', 'yes']: final_ordered = True
                    elif val in ['false', '0', 'f', 'n', 'no']: final_ordered = False

                interaction = InteractionLog(id=row['id'], user_id=row['user_id'], restaurant_id=row['restaurant_id'], recommendation_rank=int(row['recommendation_rank']) if pd.notna(row['recommendation_rank']) else None, user_action=row['user_action'], timestamp=timestamp, swipe_time_sec=int(row['swipe_time_sec']) if pd.notna(row['swipe_time_sec']) else None, final_ordered=final_ordered, user_feedback=row['user_feedback'])
                db.session.add(interaction)
            print(f"-> {len(interactions_df)} interaction logs ready.")

            # --- FINAL COMMIT ---
            print("\nCommitting all staged data to the database...")
            db.session.commit()
            print("\n✅ Seeding complete! All data has been committed.")

        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Rolling back database changes. No data was saved.")
            db.session.rollback()

if __name__ == '__main__':
    seed_data()
