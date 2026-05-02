#!/usr/bin/env python3
"""
Email Configuration Test Script for KitabGhar
This script tests your Flask-Mail configuration without running the full app.
"""

import os
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail, Message

# Load environment variables
load_dotenv()

def test_email_config():
    """Test email configuration"""
    print("🔧 Testing KitabGhar Email Configuration")
    print("=" * 50)

    # Check environment variables
    mail_server = os.environ.get('MAIL_SERVER')
    mail_port = os.environ.get('MAIL_PORT')
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER')

    print(f"📧 MAIL_SERVER: {mail_server or 'Not set'}")
    print(f"🔌 MAIL_PORT: {mail_port or 'Not set'}")
    print(f"👤 MAIL_USERNAME: {mail_username or 'Not set'}")
    print(f"🔑 MAIL_PASSWORD: {'*' * len(mail_password) if mail_password else 'Not set'}")
    print(f"📤 MAIL_DEFAULT_SENDER: {mail_default_sender or 'Not set'}")
    print()

    # Check required fields
    if not mail_username or not mail_password:
        print("❌ ERROR: MAIL_USERNAME and MAIL_PASSWORD are required!")
        print("   Please set these values in your .env file")
        return False

    if not mail_server:
        print("⚠️  WARNING: MAIL_SERVER not set, using default (smtp.gmail.com)")

    if not mail_port:
        print("⚠️  WARNING: MAIL_PORT not set, using default (587)")

    # Create Flask app for testing
    app = Flask(__name__)

    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = mail_server or 'smtp.gmail.com'
    app.config['MAIL_PORT'] = int(mail_port or 587)
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    app.config['MAIL_USERNAME'] = mail_username
    app.config['MAIL_PASSWORD'] = mail_password
    app.config['MAIL_DEFAULT_SENDER'] = mail_default_sender or 'test@kitabghar.com'

    # Initialize Flask-Mail
    mail = Mail(app)

    print("🚀 Testing email connection...")

    try:
        with app.app_context():
            # Create a test message
            msg = Message(
                subject="KitabGhar Email Test",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[mail_username],  # Send to yourself
                body="""
This is a test email from KitabGhar.

If you received this email, your email configuration is working correctly!

Configuration Details:
- Server: {app.config['MAIL_SERVER']}
- Port: {app.config['MAIL_PORT']}
- TLS: {app.config['MAIL_USE_TLS']}
- SSL: {app.config['MAIL_USE_SSL']}

Sent from: {app.config['MAIL_DEFAULT_SENDER']}
                """.format(**app.config)
            )

            # Send the test email
            mail.send(msg)

        print("✅ SUCCESS: Test email sent successfully!")
        print(f"   📧 Check your inbox: {mail_username}")
        print("   📁 Also check your spam/junk folder")
        return True

    except Exception as e:
        print(f"❌ ERROR: Failed to send test email")
        print(f"   Details: {str(e)}")

        # Provide specific guidance based on error
        error_msg = str(e).lower()
        if 'authentication' in error_msg or 'credentials' in error_msg:
            print("\n💡 TIP: This is likely an authentication error.")
            print("   - Make sure you're using an App Password (not regular password)")
            print("   - For Gmail: Generate App Password at https://myaccount.google.com/apppasswords")
        elif 'connection' in error_msg or 'smtp' in error_msg:
            print("\n💡 TIP: This is likely a connection error.")
            print("   - Check your internet connection")
            print("   - Verify MAIL_SERVER and MAIL_PORT settings")
        elif 'tls' in error_msg or 'ssl' in error_msg:
            print("\n💡 TIP: This might be a TLS/SSL configuration issue.")
            print("   - Try toggling MAIL_USE_TLS and MAIL_USE_SSL settings")

        return False

def main():
    """Main function"""
    success = test_email_config()

    print("\n" + "=" * 50)
    if success:
        print("🎉 Email configuration test PASSED!")
        print("   Your contact form should work correctly.")
    else:
        print("⚠️  Email configuration test FAILED!")
        print("   Please check your .env file and try again.")
        print("   See README_EMAIL_SETUP.md for detailed instructions.")

    print("\n📖 For more help, read: README_EMAIL_SETUP.md")

if __name__ == "__main__":
    main()
