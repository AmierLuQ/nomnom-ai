from app import db, User, Restaurant, Meal, Review, InteractionLog, bcrypt, app  # 👈 Import all models
from dateutil import parser
import json
import datetime

def parse_date(date_str):
    try:
        # First try the expected format
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            # Try parsing MM/DD/YY or D/M/YY style
            return datetime.datetime.strptime(date_str, "%m/%d/%y").date()
        except ValueError:
            # Last resort: use dateutil parser
            return parser.parse(date_str).date()


def import_users():
    with open('data/users.json', 'r', encoding='utf-8') as f:
        users = json.load(f)

    for u in users:
        if User.query.filter_by(username=u['Username'].lower()).first():
            print(f"User {u['Username']} already exists. Skipping.")
            continue

        hashed_pw = bcrypt.generate_password_hash("abcd1234").decode('utf-8')  # Set a default password

        new_user = User(
            id=u['ID'],
            username=u['Username'].lower(),
            name=u['Name'],
            email=u['Email'].lower(),
            phone=None,
            dob=None,  # Parse if DOB exists in JSON
            age=u.get('Age'),
            gender=u.get('Gender'),
            location=u.get('Location'),
            latitude=float(u['Latitude']) if u.get('Latitude') else None,
            longitude=float(u['Longitude']) if u.get('Longitude') else None,
            last_login=None,  # Or parse u['Last Login'] if available
            password=hashed_pw
        )
        db.session.add(new_user)
        print(f"✅ Added user: {u['Username']}")
    db.session.commit()
    print("✅ All users imported successfully.\n")


def import_restaurants():
    with open('data/restaurants.json', 'r', encoding='utf-8') as f:
        restaurants = json.load(f)

    for r in restaurants:
        if Restaurant.query.filter_by(id=r['ID']).first():
            print(f"Restaurant {r['Name']} already exists. Skipping.")
            continue

        new_restaurant = Restaurant(
            id=r['ID'],
            name=r['Name'],
            district=r.get('District'),
            price_min=r.get('Est Price Min per Person'),
            price_max=r.get('Est Price Max per Person'),
            google_rating=float(r['Google Rating']) if r.get('Google Rating') else None,
            num_google_reviews=int(r['Number of Google Reviewers']) if r.get('Number of Google Reviewers') else None,
            opening_time=r.get('Opening Time'),
            closing_time=r.get('Closing Time'),
            location=r.get('Location'),
            latitude=float(r['Latitude']) if r.get('Latitude') else None,
            longitude=float(r['Longitude']) if r.get('Longitude') else None,
            tag_1=r.get('Tag 1'),
            tag_2=r.get('Tag 2'),
            tag_3=r.get('Tag 3'),
            address=r.get('Address'),
            phone=r.get('Phone No.'),
            description=r.get('Description')
        )
        db.session.add(new_restaurant)
        print(f"✅ Added restaurant: {r['Name']}")
    db.session.commit()
    print("✅ All restaurants imported successfully.\n")


def import_meals():
    with open('data/meal_data.json', 'r', encoding='utf-8') as f:
        meals = json.load(f)

    for m in meals:
        if Meal.query.filter_by(id=m['ID']).first():
            print(f"Meal {m['ID']} already exists. Skipping.")
            continue

        new_meal = Meal(
            id=m['ID'],
            user_id=m['User ID'],
            restaurant_id=m['Restaurant ID'],
            date=datetime.datetime.strptime(m['Date'], "%Y-%m-%d").date(),
            day=m.get('Day'),
            meal_time=m.get('Meal')
        )
        db.session.add(new_meal)
        print(f"✅ Added meal: {m['ID']}")
    db.session.commit()
    print("✅ All meals imported successfully.\n")


def import_reviews():
    with open('data/reviews.json', 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    for r in reviews:
        if Review.query.filter_by(id=r['ID']).first():
            print(f"Review {r['ID']} already exists. Skipping.")
            continue

        new_review = Review(
            id=r['ID'],
            user_id=r['User ID'],
            restaurant_id=r['Restaurant ID'],
            date=parse_date(r['Date']),
            rating=int(r['Rating']),
            price_satisfaction=True if r.get('Price Satisfaction') == "TRUE" else False,
            visit_frequency=int(r['Frequency of Visits']) if r.get('Frequency of Visits') else None
        )
        db.session.add(new_review)
        print(f"✅ Added review: {r['ID']}")
    db.session.commit()
    print("✅ All reviews imported successfully.\n")

def import_interaction():
    with open('data/interaction_log.json', 'r', encoding='utf-8') as f:
        logs = json.load(f)

    with app.app_context():
        for log in logs:
            # Check if this log already exists
            if InteractionLog.query.filter_by(id=log['ID']).first():
                print(f"Log {log['ID']} already exists. Skipping.")
                continue

            new_log = InteractionLog(
                id=log['ID'],
                user_id=log['User ID'],
                restaurant_id=log['Restaurant ID'],
                recommendation_rank=int(log['Recommendation Rank']) if log.get('Recommendation Rank') else None,
                user_action=log['User Action'].lower(),
                timestamp=datetime.datetime.strptime(log['Timestamp'], "%Y-%m-%d %H:%M:%S"),
                swipe_time_sec=int(log['Swipe Time (Sec)']) if log.get('Swipe Time (Sec)') else None,
                final_ordered=True if log['Final Ordered'] == "TRUE" else False,
                user_feedback=log['User Feedback']
            )
            db.session.add(new_log)
            print(f"✅ Added interaction log: {log['ID']}")

        db.session.commit()
        print("✅ All interaction logs imported successfully.")

# 🚀 Run all imports
if __name__ == "__main__":
    with app.app_context():
        import_users()
        import_restaurants()
        import_meals()
        import_reviews()
        import_interaction()
