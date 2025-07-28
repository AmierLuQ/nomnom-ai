# =======================================================================
# NomNom AI: Direct Database Seeder
# This script connects directly to the database for robust seeding.
# It should be run from the `scripts` directory.
# =======================================================================

# --- Path Correction ---
# Allows the script to find the main 'app' module from the parent directory
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ---------------------

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from flask_bcrypt import Bcrypt
import numpy as np # Import numpy for NaN checking

# A simple bcrypt instance for hashing, independent of the Flask app
bcrypt = Bcrypt()

def run_seeder():
    """
    Main function to connect, seed, and verify the database.
    """
    print("--- Direct Seeder Initializing ---")
    
    # --- Load Environment Variables ---
    # Looks for the .env file in the parent directory (project root)
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in .env file. Please ensure it is set correctly.")
        sys.exit(1)

    # Adjust URL for SQLAlchemy if needed
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to database: {db_url[:50]}...")
    try:
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        print("Engine and Session configured successfully.")
    except Exception as e:
        print(f"❌ ERROR: Failed to create database engine. {e}")
        sys.exit(1)

    # --- Step 1: Ensure tables exist using the app context ---
    try:
        from app import db, create_app
        app = create_app() # Create an app instance to get the context
        with app.app_context():
            print("\n--- Ensuring tables exist ---")
            db.drop_all() # Wipe the database completely
            db.create_all() # Recreate the schema from models.py
            print("Tables created successfully.")
    except Exception as e:
        print(f"❌ ERROR: Could not create tables using app context. {e}")
        sys.exit(1)

    # --- Step 2: Seed the data ---
    session = None
    try:
        session = Session()
        
        print("\n--- Inserting New Data ---")
        
        # --- Users (with password hashing and data cleaning) ---
        users_df = pd.read_csv('data/users.csv')
        
        # FIX: Pre-process the dataframe to handle potential NaT/NaN values
        # Convert date/datetime columns to object type to allow for None
        for col in ['dob', 'last_login', 'created_at']:
            if col in users_df.columns:
                users_df[col] = users_df[col].astype(object).where(pd.notna(users_df[col]), None)

        user_records = users_df.to_dict('records')
        
        from app.models import User
        for record in user_records:
            password_str = str(record['password']) if pd.notna(record['password']) else "default_password"
            record['password'] = bcrypt.generate_password_hash(password_str).decode('utf-8')
            new_user = User(**record)
            session.add(new_user)

        print(f"-> Staged {len(user_records)} users for insertion.")
        
        # --- Commit the users first to satisfy foreign key constraints ---
        print("--- Committing users to the database... ---")
        session.commit()
        print("✅ Users committed successfully.")

        # --- Other tables (can use fast to_sql method) ---
        restaurants_df = pd.read_csv('data/restaurants.csv').replace({pd.NA: None})
        restaurants_df.to_sql('restaurant', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(restaurants_df)} restaurants.")
        
        meals_df = pd.read_csv('data/meals.csv').replace({pd.NA: None})
        meals_df.to_sql('meal', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(meals_df)} meals.")
        
        reviews_df = pd.read_csv('data/reviews.csv').replace({pd.NA: None})
        reviews_df.to_sql('review', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(reviews_df)} reviews.")
        
        interactions_df = pd.read_csv('data/interaction_logs.csv').replace({pd.NA: None})
        interactions_df.to_sql('interaction_log', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(interactions_df)} interactions.")

        print("\n✅ Seeding complete! All data has been committed.")

    except Exception as e:
        print(f"\n❌ An error occurred during seeding: {e}")
        if session:
            print("Rolling back transaction.")
            session.rollback()
    finally:
        if session:
            session.close()
            print("Seeding session closed.")

    # --- Step 3: Verify the data ---
    verification_session = None
    try:
        verification_session = Session()
        print("\n--- Verification Step ---")
        user_count = verification_session.execute(text('SELECT COUNT(*) FROM "user";')).scalar()
        restaurant_count = verification_session.execute(text('SELECT COUNT(*) FROM restaurant;')).scalar()
        
        print(f"Verification query found {user_count} users in the database.")
        print(f"Verification query found {restaurant_count} restaurants in the database.")
        
        if user_count > 0:
            print("\n🎉 SUCCESS: Data has been successfully written and verified in the remote database!")
        else:
            print("\n🔥 FAILURE: The database is still empty after the script ran. The commit did not persist.")
            
    except Exception as e:
        print(f"❌ An error occurred during verification: {e}")
    finally:
        if verification_session:
            verification_session.close()
            print("Verification session closed.")


if __name__ == '__main__':
    run_seeder()
