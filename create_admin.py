from app import app, db
from models import User

def create_admin_user():
    with app.app_context():
        admin_email = "simapan1996@gmail.com"
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            print("Admin user already exists.")
            return
        admin_user = User(
            username="admin",
            email=admin_email,
            role="admin",
            first_name="Admin",
            last_name="User"
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully.")

if __name__ == "__main__":
    create_admin_user()
