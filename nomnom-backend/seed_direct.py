import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

def run_seeder():
    """
    Main function to connect, seed, and verify the database.
    """
    print("--- Direct Seeder Initializing ---")
    load_dotenv()

    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in .env file. Please ensure it is set correctly.")
        sys.exit(1) # Exit the script with an error code

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
        from app import db, app
        with app.app_context():
            print("\n--- Ensuring tables exist ---")
            db.create_all()
            print("Table check complete.")
    except Exception as e:
        print(f"❌ ERROR: Could not create tables using app context. {e}")
        sys.exit(1)

    # --- Step 2: Seed the data ---
    session = None # Initialize session to None
    try:
        session = Session() # Create a new session for this transaction
        
        print("\n--- Wiping Data ---")
        session.execute(text('DELETE FROM interaction_log;'))
        session.execute(text('DELETE FROM review;'))
        session.execute(text('DELETE FROM meal;'))
        session.execute(text('DELETE FROM restaurant;'))
        session.execute(text('DELETE FROM "user";'))
        print("All existing data wiped from tables.")
        
        print("\n--- Inserting New Data ---")
        users_df = pd.read_csv('users.csv').replace({pd.NA: None})
        users_df.to_sql('user', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(users_df)} users.")

        restaurants_df = pd.read_csv('restaurants.csv').replace({pd.NA: None})
        restaurants_df.to_sql('restaurant', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(restaurants_df)} restaurants.")
        
        meals_df = pd.read_csv('meals.csv').replace({pd.NA: None})
        meals_df.to_sql('meal', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(meals_df)} meals.")
        
        reviews_df = pd.read_csv('reviews.csv').replace({pd.NA: None})
        reviews_df.to_sql('review', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(reviews_df)} reviews.")
        
        interactions_df = pd.read_csv('interaction_logs.csv').replace({pd.NA: None})
        interactions_df.to_sql('interaction_log', engine, if_exists='append', index=False)
        print(f"-> Inserted {len(interactions_df)} interactions.")

        print("\n--- Committing Transaction ---")
        session.commit()
        print("✅ Data committed successfully.")

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