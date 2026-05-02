from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))

        if current_user.role != 'admin':
            flash('Admin access required.', 'error')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function

def author_required(f):
    """Decorator to require author or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_author():
            flash('Author or Admin access required to upload books.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def owns_book_or_admin(f):
    """Decorator to check if user owns the book or is admin"""
    @wraps(f)
    def decorated_function(id, *args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        from models import Ebook
        book = Ebook.query.get_or_404(id)
        
        # Allow if user is admin or book uploader
        if current_user.is_admin() or (book.uploaded_by and book.uploaded_by == current_user.id):
            return f(id, *args, **kwargs)
        
        flash('You can only modify books you have uploaded.', 'error')
        abort(403)
    return decorated_function