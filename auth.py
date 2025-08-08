from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from models import User
import re

# Create auth blueprint
auth = Blueprint('auth', __name__, url_prefix='/auth')

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
        
        # Try to find user by username or email
        user = None
        if is_valid_email(username_or_email):
            user = User.query.filter_by(email=username_or_email.lower()).first()
        else:
            user = User.query.filter_by(username=username_or_email).first()
        
        if user and user.check_password(password) and user.is_active:
            # Update last login
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=remember_me)
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
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
        role = request.form.get('role', 'Reader')
        
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
        
        if role not in ['Reader', 'Author']:
            role = 'Reader'  # Default to Reader
        
        # Check for existing users
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
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
            return redirect(url_for('home'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    """User logout"""
    user_name = current_user.get_full_name()
    logout_user()
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('home'))

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
        
        # Validation
        errors = []
        
        if email != current_user.email:
            if not is_valid_email(email):
                errors.append('Please enter a valid email address.')
            elif User.query.filter(User.email == email, User.id != current_user.id).first():
                errors.append('Email already registered by another user.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/edit_profile.html')
        
        # Update user
        try:
            current_user.first_name = first_name or None
            current_user.last_name = last_name or None
            current_user.email = email
            
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