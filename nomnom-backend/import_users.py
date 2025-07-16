from app import db, User, bcrypt, app  # 👈 import your Flask app
import json

# Load JSON
with open('data/users.json', 'r', encoding='utf-8') as f:
    users = json.load(f)

with app.app_context():  # 👈 Enter Flask app context
    for u in users:
        # Check if user already exists to avoid duplicates
        if User.query.filter_by(username=u['Username'].lower()).first():
            print(f"User {u['Username']} already exists. Skipping.")
            continue

        hashed_pw = bcrypt.generate_password_hash("default123").decode('utf-8')  # Set a default password

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
            latitude=u.get('Latitude'),
            longitude=u.get('Longitude'),
            last_login=None,  # Parse u['Last Login'] if needed
            password=hashed_pw
        )
        db.session.add(new_user)
        print(f"Added user: {u['Username']}")

    db.session.commit()
    print("✅ All users imported successfully.")
