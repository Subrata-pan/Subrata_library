import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

from extensions import db

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Upload folder setup
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure the database
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    if os.environ.get("RENDER"):
        raise RuntimeError("DATABASE_URL must be set to a Render PostgreSQL connection string.")
    database_url = "sqlite:///instance/kitabghar.db"

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}
if database_url.startswith("postgresql://"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_recycle"] = 300
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config["WTF_CSRF_SSL_STRICT"] = os.environ.get("WTF_CSRF_SSL_STRICT", "False").lower() == "true"

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@kitabghar.com')

# Validate required email configuration
if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
    print("WARNING: Email configuration incomplete. Please set MAIL_USERNAME and MAIL_PASSWORD in your .env file.")
    print("Contact form will not send emails until email is properly configured.")

# Initialize extensions
db.init_app(app)
mail = Mail(app)
csrf = CSRFProtect(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models, auth, and routes
    import models  # noqa: F401
    import auth  # noqa: F401
    import routes  # noqa: F401
    import services  # noqa: F401

    # Register auth blueprint
    app.register_blueprint(auth.auth)
    app.register_blueprint(services.api, url_prefix='/api')

    # Create all tables
    db.create_all()

    # Optionally create/update an admin user from environment variables.
    try:
        auth.ensure_admin_user()
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to create or update the configured admin user.")
