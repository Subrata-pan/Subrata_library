from app import create_app
from extensions import db
from models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='simapan1996@gmail.com').first()
    if user:
        print(f"User found: {user}")
        print(f"Password hash: {user.password_hash}")
        print(f"Role: {user.role}")
        print(f"Email: {user.email}")
    else:
        print("Admin user not found.")
