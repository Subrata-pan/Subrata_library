#!/usr/bin/env python3
"""
User Management Script for KitabGhar
Provides CLI commands for managing users in the database using argparse.
"""

import os
import sys
import argparse
from flask import Flask

# Add current directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///instance/kitabghar.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    from extensions import db
    db.init_app(app)

    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        import models

    return app, db

def delete_user(args):
    """Delete a user from the database by email address"""
    app, db = create_app()

    with app.app_context():
        from models import User
        try:
            # Find the user
            user = User.query.filter_by(email=args.email.lower()).first()

            if not user:
                print(f"❌ User not found with email: {args.email}")
                return

            # Show user details
            print(f"📋 Found user:")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Full Name: {user.get_full_name()}")
            print(f"   Role: {user.role}")
            print(f"   Created: {user.created_date}")

            # Confirm deletion
            if not args.confirm:
                response = input(f"⚠️  Are you sure you want to delete user '{user.username}'? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("❌ Deletion cancelled.")
                    return

            # Delete the user
            db.session.delete(user)
            db.session.commit()

            print(f"✅ User '{user.username}' ({args.email}) has been successfully deleted.")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting user: {str(e)}")
            sys.exit(1)

def list_users(args):
    """List all users in the database"""
    app, db = create_app()

    with app.app_context():
        from models import User
        try:
            users = User.query.order_by(User.created_date.desc()).all()

            if not users:
                print("📋 No users found in database.")
                return

            print(f"📋 Total Users: {len(users)}")
            print("-" * 80)
            print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Status':<10} {'Created':<20}")
            print("-" * 80)

            for user in users:
                status = "✅ Active" if user.is_active else "❌ Inactive"
                created_str = user.created_date.strftime("%Y-%m-%d %H:%M") if user.created_date else "N/A"
                print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10} {status:<10} {created_str:<20}")

        except Exception as e:
            print(f"❌ Error listing users: {str(e)}")
            sys.exit(1)

def create_admin(args):
    """Create a new admin user if not exists"""
    app, db = create_app()

    with app.app_context():
        from models import User
        try:
            # Check if admin already exists
            existing_admin = User.query.filter_by(email=args.email.lower()).first()

            if existing_admin:
                print(f"❌ Admin user with email '{args.email}' already exists.")
                print(f"   Username: {existing_admin.username}")
                print(f"   Role: {existing_admin.role}")
                return

            # Create new admin user
            admin_user = User(
                username=args.username,
                email=args.email.lower(),
                role='Admin',
                first_name=args.first_name,
                last_name=args.last_name
            )
            admin_user.set_password(args.password)

            db.session.add(admin_user)
            db.session.commit()

            print(f"✅ Admin user '{args.username}' created successfully!")
            print(f"   Email: {args.email}")
            print(f"   Full Name: {admin_user.get_full_name()}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {str(e)}")
            sys.exit(1)

def main():
    """Main function to parse arguments and execute commands"""
    parser = argparse.ArgumentParser(
        description='User Management Script for KitabGhar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_users.py delete_user --email user@example.com
  python manage_users.py list_users
  python manage_users.py create_admin --username admin --email admin@example.com --password securepass
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Delete user command
    delete_parser = subparsers.add_parser('delete_user', help='Delete a user by email')
    delete_parser.add_argument('--email', required=True, help='Email address of the user to delete')
    delete_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    delete_parser.set_defaults(func=delete_user)

    # List users command
    list_parser = subparsers.add_parser('list_users', help='List all users')
    list_parser.set_defaults(func=list_users)

    # Create admin command
    create_parser = subparsers.add_parser('create_admin', help='Create a new admin user')
    create_parser.add_argument('--username', required=True, help='Username for the admin')
    create_parser.add_argument('--email', required=True, help='Email address for the admin')
    create_parser.add_argument('--password', required=True, help='Password for the admin')
    create_parser.add_argument('--first-name', default='', help='First name (optional)')
    create_parser.add_argument('--last-name', default='', help='Last name (optional)')
    create_parser.set_defaults(func=create_admin)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute the appropriate function
    args.func(args)

if __name__ == '__main__':
    main()
