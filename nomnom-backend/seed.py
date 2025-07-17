import pandas as pd
from app import app, db, User, Restaurant, Meal, Review, InteractionLog, bcrypt
from dotenv import load_dotenv
import os
from datetime import datetime
import numpy as np

load_dotenv() 

def seed_data():
    """
    Drops all existing data, recreates tables, and populates them from CSV files.
    """
    print("Starting the seeding process...")
    
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Tables created successfully.")

        try:
            # --- 1. Seed Users ---
            print("\nSeeding users...")
            users_df = pd.read_csv('users.csv')
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
            db.session.commit()
            print(f"✅ Successfully seeded {len(users_df)} users.")

            # --- 2. Seed Restaurants ---
            print("\nSeeding restaurants...")
            restaurants_df = pd.read_csv('restaurants.csv').replace({np.nan: None})
            for _, row in restaurants_df.iterrows():
                restaurant = Restaurant(**row.to_dict())
                db.session.add(restaurant)
            db.session.commit()
            print(f"✅ Successfully seeded {len(restaurants_df)} restaurants.")

            # --- 3. Seed Meals ---
            print("\nSeeding meals...")
            meals_df = pd.read_csv('meals.csv').replace({np.nan: None})
            for _, row in meals_df.iterrows():
                meal_date = None
                if pd.notna(row['date']):
                    try:
                        meal_date = datetime.strptime(str(row['date']), '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse date '{row['date']}' for meal {row['id']}.")
                meal = Meal(id=row['id'], user_id=row['user_id'], restaurant_id=row['restaurant_id'], date=meal_date, day=row['day'], meal_time=row['meal_time'])
                db.session.add(meal)
            db.session.commit()
            print(f"✅ Successfully seeded {len(meals_df)} meals.")

            # --- 4. Seed Reviews ---
            print("\nSeeding reviews...")
            reviews_df = pd.read_csv('reviews.csv').replace({np.nan: None})
            for _, row in reviews_df.iterrows():
                review_date = None
                if pd.notna(row['date']):
                    try:
                        review_date = datetime.strptime(str(row['date']), '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse date '{row['date']}' for review {row['id']}.")
                review = Review(id=row['id'], user_id=row['user_id'], restaurant_id=row['restaurant_id'], date=review_date, rating=int(row['rating']), price_satisfaction=bool(row['price_satisfaction']) if pd.notna(row['price_satisfaction']) else None, visit_frequency=int(row['visit_frequency']) if pd.notna(row['visit_frequency']) else None)
                db.session.add(review)
            db.session.commit()
            print(f"✅ Successfully seeded {len(reviews_df)} reviews.")

            # --- 5. Seed Interaction Logs ---
            print("\nSeeding interaction logs...")
            interactions_df = pd.read_csv('interaction_logs.csv').replace({np.nan: None})
            for _, row in interactions_df.iterrows():
                timestamp = None
                if pd.notna(row['timestamp']):
                    try:
                        # Assuming timestamp is in a common format like 'YYYY-MM-DD HH:MM:SS'
                        timestamp = datetime.strptime(str(row['timestamp']), '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse timestamp '{row['timestamp']}' for log {row['id']}.")
                
                # Robustly handle boolean conversion
                final_ordered = None
                if pd.notna(row['final_ordered']):
                    val = str(row['final_ordered']).lower()
                    if val in ['true', '1', 't', 'y', 'yes']:
                        final_ordered = True
                    elif val in ['false', '0', 'f', 'n', 'no']:
                        final_ordered = False

                interaction = InteractionLog(
                    id=row['id'],
                    user_id=row['user_id'],
                    restaurant_id=row['restaurant_id'],
                    recommendation_rank=int(row['recommendation_rank']) if pd.notna(row['recommendation_rank']) else None,
                    user_action=row['user_action'],
                    timestamp=timestamp,
                    swipe_time_sec=int(row['swipe_time_sec']) if pd.notna(row['swipe_time_sec']) else None,
                    final_ordered=final_ordered,
                    user_feedback=row['user_feedback']
                )
                db.session.add(interaction)
            db.session.commit()
            print(f"✅ Successfully seeded {len(interactions_df)} interaction logs.")


            print("\n🎉 Seeding complete!")

        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Rolling back database changes.")
            db.session.rollback()

if __name__ == '__main__':
    seed_data()