from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, func
from extensions import db
from models import User
import re
import os
from authlib.integrations.flask_client import OAuth

# Create auth blueprint
auth = Blueprint('auth', __name__, url_prefix='/auth')
oauth = OAuth()

def get_google_oauth_config(app):
    """Read Google OAuth settings from config or environment variables."""
    client_id = (
        app.config.get('GOOGLE_CLIENT_ID')
        or os.environ.get('GOOGLE_CLIENT_ID')
        or os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        or ''
    ).strip()
    client_secret = (
        app.config.get('GOOGLE_CLIENT_SECRET')
        or os.environ.get('GOOGLE_CLIENT_SECRET')
        or os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        or ''
    ).strip()
    return client_id, client_secret

def get_admin_email():
    """Return the configured admin email in normalized form."""
    return os.environ.get("ADMIN_EMAIL", "simapan1996@gmail.com").strip().lower()

def build_unique_username(email, name):
    """Create a unique username for Google sign-ins."""
    base_username = (email.split('@')[0] if email else name or 'user').replace(' ', '_')
    base_username = re.sub(r'[^a-zA-Z0-9_]', '_', base_username).strip('_') or 'user'
    username = base_username
    suffix = 1

    while User.query.filter_by(username=username).first():
        suffix += 1
        username = f'{base_username}_{suffix}'

    return username

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))

        if not username_or_email or not password:
            flash('Please enter both username/email and password.', 'error')
            return render_template('auth/login.html')

        login_identifier = username_or_email.lower()
        user = User.query.filter(
            or_(
                func.lower(User.email) == login_identifier,
                func.lower(User.username) == login_identifier
            )
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is inactive. Please contact the administrator.', 'error')
                return render_template('auth/login.html')

            # Force role to admin if email matches the configured owner account.
            if user.email.lower() == get_admin_email():
                user.role = "admin"
            else:
                user.role = "user"

            from datetime import datetime
            user.last_login = datetime.utcnow()
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            login_user(user, remember=remember_me)
            session["role"] = user.role
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            if user.role == "admin":
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid username/email or password.', 'error')

    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', 'user')

        # Validation
        errors = []

        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')

        if not email or not is_valid_email(email):
            errors.append('Please enter a valid email address.')

        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')

        if password != confirm_password:
            errors.append('Passwords do not match.')

        if role not in ['user']:
            role = 'user'  # Default to user

        # Check for existing users
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists. Please log in with that account.', 'info')
            return redirect(url_for("auth.login"))

        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html',
                                 username=username,
                                 email=email,
                                 first_name=first_name,
                                 last_name=last_name,
                                 role=role)

        # Create new user
        try:
            # Force role to admin if email matches the configured owner account.
            if email == get_admin_email():
                role = "admin"
            else:
                role = "user"

            user = User(
                username=username,
                email=email,
                role=role,
                first_name=first_name or None,
                last_name=last_name or None
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash(f'Registration successful! Welcome to KitabGhar, {user.get_full_name()}!', 'success')
            login_user(user)
            session["role"] = user.role
            return redirect(url_for('home'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('auth.login'))

@auth.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html')

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        profile_image = request.files.get('profile_image')

        # Validation
        errors = []

        if email != current_user.email:
            if not is_valid_email(email):
                errors.append('Please enter a valid email address.')
            elif User.query.filter(User.email == email, User.id != current_user.id).first():
                errors.append('Email already registered by another user.')

        # Validate profile image if uploaded
        if profile_image and profile_image.filename != '':
            filename = profile_image.filename.lower()
            if not (filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg')):
                errors.append('Only PNG and JPG images are allowed for profile picture.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/edit_profile.html')

        # Update user
        try:
            current_user.first_name = first_name or None
            current_user.last_name = last_name or None
            current_user.email = email

            # Handle profile image upload
            if profile_image and profile_image.filename != '':
                from werkzeug.utils import secure_filename
                from PIL import Image
                import os

                filename = secure_filename(profile_image.filename)
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                upload_path = os.path.join(upload_folder, filename)
                profile_image.save(upload_path)

                # Resize and crop image to 100x100 px
                img = Image.open(upload_path)
                img = img.convert('RGB')
                img.thumbnail((100, 100))
                img.save(upload_path)

                current_user.profile_image = filename

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')

    return render_template('auth/edit_profile.html')

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not current_user.check_password(current_password):
            errors.append('Current password is incorrect.')
        
        if not new_password or len(new_password) < 6:
            errors.append('New password must be at least 6 characters long.')
        
        if new_password != confirm_password:
            errors.append('New passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while changing your password.', 'error')
    
    return render_template('auth/change_password.html')

@auth.record_once
def on_load(state):
    app = state.app
    oauth.init_app(app)
    client_id, client_secret = get_google_oauth_config(app)
    app.config['GOOGLE_CLIENT_ID'] = client_id
    app.config['GOOGLE_CLIENT_SECRET'] = client_secret

    if client_id and client_secret:
        oauth.register(
            name='google',
            client_id=client_id,
            client_secret=client_secret,
            client_kwargs={'scope': 'openid email profile'},
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
        )

@auth.route('/google')
def google_login():
    if 'google' not in oauth._clients:
        flash('Google Sign-In is not configured.', 'error')
        return redirect(url_for('auth.login'))

    scheme = 'http' if request.host.startswith(('localhost', '127.0.0.1')) else request.scheme
    redirect_uri = url_for('auth.google_auth', _external=True, _scheme=scheme)
    return oauth.google.authorize_redirect(redirect_uri)

@auth.route('/google/callback')
def google_auth():
    if 'google' not in oauth._clients:
        flash('Google Sign-In is not configured.', 'error')
        return redirect(url_for('auth.login'))
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get('userinfo') or oauth.google.parse_id_token(token)
    except Exception:
        flash('Google Sign-In failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

    if not userinfo:
        flash('Failed to authenticate with Google.', 'error')
        return redirect(url_for('auth.login'))

    email = userinfo.get('email')
    if not email:
        flash('Google did not return an email address for this account.', 'error')
        return redirect(url_for('auth.login'))

    email = email.lower()
    name = userinfo.get('name')
    given_name = userinfo.get('given_name')
    family_name = userinfo.get('family_name')
    user = User.query.filter_by(email=email).first()
    if not user:
        username = build_unique_username(email, name)
        user = User(username=username, email=email, role='user', first_name=given_name, last_name=family_name)
        user.set_password(os.urandom(16).hex())
        db.session.add(user)
        db.session.commit()
    if user.email.lower() == get_admin_email():
        user.role = "admin"
    else:
        user.role = "user"
    db.session.commit()
    session["role"] = user.role
    login_user(user)
    flash(f'Logged in as {user.get_full_name()} via Google.', 'success')
    return redirect(url_for('home'))
