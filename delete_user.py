#!/usr/bin/env python3
"""
Script to delete a user from the KitabGhar database by email
"""

import sqlite3
import os

def delete_user_by_email(email):
    """Delete a user from the database by email address"""
    db_path = "instance/kitabghar.db"

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # First, check if the user exists
        cursor.execute("SELECT id, username, email FROM user WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            user_id, username, user_email = user
            print(f"🔍 Found user: ID={user_id}, Username={username}, Email={user_email}")

            # Delete the user
            cursor.execute("DELETE FROM user WHERE email = ?", (email,))
            conn.commit()

            # Check if deletion was successful
            if cursor.rowcount > 0:
                print(f"✅ Successfully deleted user with email: {email}")
                return True
            else:
                print(f"⚠️  No user was deleted (email: {email})")
                return False
        else:
            print(f"⚠️  User with email '{email}' not found in the database")
            return False

    except sqlite3.Error as e:
        print(f"❌ SQLite error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    # Email to delete
    target_email = 'simapan1996@gmail.com'

    print(f"🗑️  Attempting to delete user with email: {target_email}")
    print("-" * 50)

    success = delete_user_by_email(target_email)

    if success:
        print("\n✅ User deletion completed successfully")
    else:
        print("\n❌ User deletion failed or user not found")
