import os
from flask import render_template, request, redirect, url_for, flash, send_file, abort, jsonify
from models import Ebook as Book  # Use Ebook model as Book alias
from flask_login import login_required, current_user
from app import app
from extensions import db
from flask import abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func
from app import app
from extensions import db
try:
    from models import Ebook, Category, User, ReadingHistory, Notification, Favorite, SavedBook
except ImportError:
    from __main__ import Ebook, Category, User, ReadingHistory, Notification, Favorite, SavedBook
from decorators import author_required, owns_book_or_admin

ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
ADMIN_EMAIL = 'simapan1996@gmail.com'  # Owner's email

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image_file(filename):
    """Check if the file has an allowed image extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def is_owner():
    """Check if current user is the library owner"""
    return current_user.is_authenticated and current_user.email == ADMIN_EMAIL

def can_view_book(book):
    """Allow approved books to everyone, pending/rejected only to admin or uploader."""
    if book.status == 'approved':
        return True
    if not current_user.is_authenticated:
        return False
    return current_user.role == 'admin' or book.uploaded_by == current_user.id

@app.route('/')
def home():
    """Home page with recent uploads and statistics"""
    recent_books = Ebook.query.filter_by(status='approved').order_by(Ebook.upload_date.desc()).limit(5).all()
    total_books = Ebook.query.filter_by(status='approved').count()
    total_categories = Category.query.count()

    # Get category statistics
    category_stats = db.session.query(
        Ebook.category,
        func.count(Ebook.id).label('count')
    ).group_by(Ebook.category).filter(Ebook.category.isnot(None), Ebook.status == 'approved').all()
    
    return render_template('index.html', 
                         recent_books=recent_books,
                         total_books=total_books,
                         total_categories=total_categories,
                         category_stats=category_stats)

@app.route('/notifications')
@login_required
def notifications():
    """View user notifications"""
    try:
        user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
        if request.accept_mimetypes.best == 'application/json':
            return jsonify([{
                'id': n.id,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat() if n.created_at else None
            } for n in user_notifications])

        unread_notifications = [n for n in user_notifications if not n.is_read]
        for notification in unread_notifications:
            notification.is_read = True
        if unread_notifications:
            db.session.commit()

        return render_template('notifications.html', notifications=user_notifications)
    except Exception:
        if request.accept_mimetypes.best == 'application/json':
            return jsonify([])
        flash('Unable to load notifications right now. Please try again.', 'error')
        return render_template('notifications.html', notifications=[])

@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        abort(403)
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_authenticated or current_user.role != 'admin':
        abort(403)
    total_pending = Book.query.filter_by(status='pending').count()
    total_approved = Book.query.filter_by(status='approved').count()
    total_rejected = Book.query.filter_by(status='rejected').count()
    pending_books = Book.query.filter_by(status='pending').all()
    approved_books = Book.query.filter_by(status='approved').all()
    return render_template('admin_dashboard.html',
                           total_pending=total_pending,
                           total_approved=total_approved,
                           total_rejected=total_rejected,
                           pending_books=pending_books,
                           approved_books=approved_books)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload a new ebook"""
    if not current_user.is_authenticated:
        flash('Please log in to upload books.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # Validate CSRF token
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as e:
            flash('CSRF token validation failed. Please try again.', 'error')
            return render_template('upload.html', categories=Category.query.order_by(Category.name).all())
        try:
            # Validate form data
            title = request.form.get('title', '').strip()
            author = request.form.get('author', '').strip()
            category = request.form.get('category', '').strip()
            language = request.form.get('language', '').strip()
            description = request.form.get('description', '').strip()
            
            if not title:
                flash('Title is required!', 'error')
                return render_template('upload.html')
            
            # Check if file was uploaded
            if 'ebook' not in request.files:
                flash('No file selected!', 'error')
                return render_template('upload.html')
            
            file = request.files['ebook']
            if file.filename == '':
                flash('No file selected!', 'error')
                return render_template('upload.html')
            
            # Validate file type
            if not allowed_file(file.filename):
                flash('Only PDF files are allowed!', 'error')
                return render_template('upload.html')
            
            # Save the file
            filename = secure_filename(file.filename)
            # Add timestamp to avoid filename conflicts
            import time
            timestamp = str(int(time.time()))
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            # Create category if it doesn't exist
            if category:
                existing_category = Category.query.filter_by(name=category).first()
                if not existing_category:
                    new_category = Category(name=category)
                    db.session.add(new_category)
            
            # Handle cover image upload
            cover_filename = None
            if 'cover' in request.files:
                cover_file = request.files['cover']
                if cover_file.filename != '':
                    if not allowed_image_file(cover_file.filename):
                        flash('Only JPG, PNG, and GIF images are allowed for cover!', 'error')
                        return render_template('upload.html', categories=Category.query.order_by(Category.name).all())

                    # Check cover file size (5MB limit)
                    cover_file.seek(0, 2)  # Seek to end
                    cover_size = cover_file.tell()
                    cover_file.seek(0)  # Seek back to beginning
                    if cover_size > 5 * 1024 * 1024:
                        flash('Cover image size exceeds 5MB limit!', 'error')
                        return render_template('upload.html', categories=Category.query.order_by(Category.name).all())

                    # Save cover image
                    cover_filename = secure_filename(cover_file.filename)
                    cover_file.save(os.path.join(app.config['UPLOAD_FOLDER'], cover_filename))

            initial_status = 'approved' if current_user.role == 'admin' else 'pending'

            # Save ebook info to database
            new_ebook = Ebook(
                title=title,
                author=author or None,
                category=category or None,
                language=language or None,
                file_path=filepath,
                filename=filename,
                file_size=file_size,
                cover=cover_filename,
                description=description or None,
                uploaded_by=current_user.id,
                status=initial_status
            )
            
            db.session.add(new_ebook)
            db.session.commit()
            
            if initial_status == 'pending':
                flash(f"'{title}' has been successfully uploaded and is waiting for admin approval.", 'info')
            else:
                flash(f"'{title}' has been successfully uploaded!", 'success')
            return redirect(url_for('book_detail', id=new_ebook.id))
            
        except Exception as e:
            app.logger.error(f"Upload error: {str(e)}")
            flash('An error occurred while uploading the file. Please try again.', 'error')
            db.session.rollback()
    
    # Get existing categories for the dropdown
    categories = Category.query.order_by(Category.name).all()
    return render_template('upload.html', categories=categories)

@app.route('/browse')
@login_required
def browse():
    """Browse all ebooks with search and filtering"""
    if not current_user.is_authenticated:
        flash('Please log in to browse books.', 'error')
        return redirect(url_for('auth.login'))
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    language_filter = request.args.get('language', '').strip()
    sort_by = request.args.get('sort', 'recent')  # recent, title, author
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    # Base query - show approved books to regular users, approved + pending to admins
    if current_user.is_authenticated and current_user.role == 'admin':
        query = Ebook.query.filter(Ebook.status.in_(['approved', 'pending']))
    else:
        query = Ebook.query.filter_by(status='approved')
    
    # Apply search filter
    if search:
        search_filter = or_(
            Ebook.title.ilike(f'%{search}%'),
            Ebook.author.ilike(f'%{search}%'),
            Ebook.description.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    # Apply category filter
    if category_filter:
        query = query.filter(Ebook.category == category_filter)
    
    # Apply language filter
    if language_filter:
        query = query.filter(Ebook.language == language_filter)
    
    # Publication date filter (using upload_date as proxy)
    if from_date:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(from_date)
            query = query.filter(Ebook.upload_date >= dt)
        except Exception:
            pass
    if to_date:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(to_date)
            query = query.filter(Ebook.upload_date <= dt)
        except Exception:
            pass

    # Apply sorting
    if sort_by == 'title':
        query = query.order_by(Ebook.title.asc())
    elif sort_by == 'author':
        query = query.order_by(Ebook.author.asc())
    else:  # recent
        query = query.order_by(Ebook.upload_date.desc())
    
    # Paginate results
    per_page = 12
    books = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Get all categories for filter dropdown
    categories = db.session.query(Ebook.category).distinct().filter(
        Ebook.category.isnot(None)
    ).order_by(Ebook.category).all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Get all languages for filter dropdown
    languages = db.session.query(Ebook.language).distinct().filter(
        Ebook.language.isnot(None)
    ).order_by(Ebook.language).all()
    languages = [lang[0] for lang in languages if lang[0]]
    
    return render_template('browse.html', 
                         books=books,
                         categories=categories,
                         languages=languages,
                         current_search=search,
                         current_category=category_filter,
                         current_language=language_filter,
                         current_sort=sort_by)

@app.route('/book/<int:id>')
@login_required
def book_detail(id):
    """Display detailed information about a specific book"""
    if not current_user.is_authenticated:
        flash('Please log in to view book details.', 'error')
        return redirect(url_for('auth.login'))
    book = Ebook.query.get_or_404(id)
    if not can_view_book(book):
        flash('This book is waiting for admin approval.', 'warning')
        return redirect(url_for('home'))
    return render_template('book_detail.html', book=book)

@app.route('/read/<int:id>')
@login_required
def read_book(id):
    """Read a book online with PDF viewer"""
    book = Ebook.query.get_or_404(id)

    # Check if user can access this book
    if book.status == 'pending':
        # Only admin can preview pending books
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. You cannot preview pending books.', 'error')
            return redirect(url_for('home'))
    elif book.status == 'rejected':
        # No one can access rejected books except admin
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. This book is not available.', 'error')
            return redirect(url_for('home'))

    if not os.path.exists(book.file_path):
        flash('File not found on server!', 'error')
        return redirect(url_for('book_detail', id=id))

    # Record reading history for recommendations (only for approved books)
    try:
        if current_user.is_authenticated and book.status == 'approved':
            history = ReadingHistory(user_id=current_user.id, ebook_id=book.id)
            db.session.add(history)
            db.session.commit()
    except Exception:
        db.session.rollback()

    return render_template('reader.html', book=book)

@app.route('/pdf/<int:id>')
@login_required
def serve_pdf(id):
    """Serve PDF file for online reading"""
    if not current_user.is_authenticated:
        abort(403)
    book = Ebook.query.get_or_404(id)
    if not can_view_book(book):
        abort(403)
    
    if not os.path.exists(book.file_path):
        abort(404)
    
    return send_file(book.file_path, 
                    mimetype='application/pdf')

@app.route('/download/<int:id>')
@login_required
def download_book(id):
    """Download a specific book"""
    book = Ebook.query.get_or_404(id)

    # Check if user can access this book
    if book.status == 'pending':
        # Only admin can download pending books
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. You cannot download pending books.', 'error')
            return redirect(url_for('home'))
    elif book.status == 'rejected':
        # No one can access rejected books except admin
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. This book is not available.', 'error')
            return redirect(url_for('home'))

    if not os.path.exists(book.file_path):
        flash('File not found on server!', 'error')
        return redirect(url_for('book_detail', id=id))

    return send_file(book.file_path,
                    as_attachment=True,
                    download_name=f"{book.title}.pdf")

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_book(id):
    """Delete a specific book (Admin only)"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('book_detail', id=id))

    book = Ebook.query.get_or_404(id)

    try:
        # Delete the file from filesystem
        if os.path.exists(book.file_path):
            os.remove(book.file_path)

        # Delete from database
        db.session.delete(book)
        db.session.commit()

        flash(f"'{book.title}' has been successfully deleted from the library!", 'success')
        return redirect(url_for('browse'))

    except Exception as e:
        app.logger.error(f"Delete error: {str(e)}")
        flash('An error occurred while deleting the book.', 'error')
        db.session.rollback()
        return redirect(url_for('book_detail', id=id))

@app.route('/categories')
@login_required
def categories():
    """List all categories"""
    if not current_user.is_authenticated:
        flash('Please log in to view categories.', 'error')
        return redirect(url_for('auth.login'))
    categories = Category.query.order_by(Category.name).all()
    
    # Get book count for each category
    category_counts = {}
    for category in categories:
        count = Ebook.query.filter_by(category=category.name, status='approved').count()
        category_counts[category.name] = count
    
    return render_template('categories.html', 
                         categories=categories,
                         category_counts=category_counts)

@app.route('/languages')
@login_required
def languages():
    """List all available languages with book counts"""
    if not current_user.is_authenticated:
        flash('Please log in to view languages.', 'error')
        return redirect(url_for('auth.login'))
    # Define supported languages with their native scripts
    supported_languages = {
        'English': {'native': 'English', 'code': 'en'},
        'Hindi': {'native': 'हिंदी', 'code': 'hi'},
        'Bengali': {'native': 'বাংলা', 'code': 'bn'},
        'Tamil': {'native': 'தமிழ்', 'code': 'ta'},
        'Telugu': {'native': 'తెలుగు', 'code': 'te'},
        'Marathi': {'native': 'मराठी', 'code': 'mr'},
        'Gujarati': {'native': 'ગુજરાતી', 'code': 'gu'},
        'Kannada': {'native': 'ಕನ್ನಡ', 'code': 'kn'},
        'Malayalam': {'native': 'മലയാളം', 'code': 'ml'},
        'Punjabi': {'native': 'ਪੰਜਾਬੀ', 'code': 'pa'},
        'Urdu': {'native': 'اردو', 'code': 'ur'},
        'Assamese': {'native': 'অসমীয়া', 'code': 'as'},
        'Oriya': {'native': 'ଓଡ଼ିଆ', 'code': 'or'},
        'Sanskrit': {'native': 'संस्कृत', 'code': 'sa'},
        'German': {'native': 'Deutsch', 'code': 'de'},
        'French': {'native': 'Français', 'code': 'fr'},
        'Spanish': {'native': 'Español', 'code': 'es'},
        'Japanese': {'native': '日本語', 'code': 'ja'},
        'Chinese': {'native': '中文', 'code': 'zh'},
        'Arabic': {'native': 'العربية', 'code': 'ar'}
    }
    
    # Get available languages from database with book counts
    available_languages = db.session.query(
        Ebook.language,
        func.count(Ebook.id).label('count')
    ).group_by(Ebook.language).filter(
        Ebook.language.isnot(None)
    ).filter(Ebook.status == 'approved').all()
    
    # Combine supported languages with counts
    language_data = []
    for language, count in available_languages:
        if language in supported_languages:
            language_data.append({
                'name': language,
                'native': supported_languages[language]['native'],
                'code': supported_languages[language]['code'],
                'count': count
            })
    
    # Add languages with zero books for display
    for lang_name, lang_info in supported_languages.items():
        if not any(l['name'] == lang_name for l in language_data):
            language_data.append({
                'name': lang_name,
                'native': lang_info['native'],
                'code': lang_info['code'],
                'count': 0
            })
    
    # Sort by name
    language_data.sort(key=lambda x: x['name'])
    
    return render_template('languages.html', languages=language_data)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_authenticated or current_user.role != "admin":
        return redirect(url_for("home"))

    # Get pending books for approval
    pending_books = Ebook.query.filter_by(status='pending').order_by(Ebook.upload_date.desc()).all()

    # Get statistics
    total_pending = len(pending_books)
    total_approved = Ebook.query.filter_by(status='approved').count()
    total_rejected = Ebook.query.filter_by(status='rejected').count()

    return render_template('admin_dashboard.html',
                         pending_books=pending_books,
                         total_pending=total_pending,
                         total_approved=total_approved,
                         total_rejected=total_rejected)

@app.route('/admin/approve/<int:book_id>', methods=['POST'])
@login_required
def approve_book(book_id):
    """Approve a pending book"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('auth.login'))

    book = Ebook.query.get_or_404(book_id)
    if book.status == 'pending':
        book.status = 'approved'
        # Create notification for the uploader
        if book.uploaded_by:
            notification = Notification(
                user_id=book.uploaded_by,
                message=f"Your book upload request for '{book.title}' has been approved and is now available in the library."
            )
            db.session.add(notification)
        db.session.commit()
        flash(f"'{book.title}' has been approved and is now available in the library.", 'success')
    else:
        flash('Book is not in pending status.', 'warning')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:book_id>', methods=['POST'])
@login_required
def reject_book(book_id):
    """Reject a pending book"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('auth.login'))

    book = Ebook.query.get_or_404(book_id)
    if book.status == 'pending':
        book.status = 'rejected'
        # Create notification for the uploader
        if book.uploaded_by:
            notification = Notification(
                user_id=book.uploaded_by,
                message=f"Your book upload request for '{book.title}' has been rejected."
            )
            db.session.add(notification)
        db.session.commit()
        flash(f"'{book.title}' has been rejected.", 'info')
    else:
        flash('Book is not in pending status.', 'warning')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:book_id>', methods=['POST'])
@login_required
def admin_delete_book(book_id):
    """Admin delete any approved book"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('auth.login'))

    book = Ebook.query.get_or_404(book_id)

    try:
        # Delete the file from filesystem
        if os.path.exists(book.file_path):
            os.remove(book.file_path)

        # Delete from database
        db.session.delete(book)
        db.session.commit()

        flash(f"'{book.title}' has been successfully deleted from the library!", 'success')
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        app.logger.error(f"Admin delete error: {str(e)}")
        flash('An error occurred while deleting the book.', 'error')
        db.session.rollback()
        return redirect(url_for('admin_dashboard'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact us page"""
    try:
        if request.method == 'POST':
            # Validate CSRF token
            from flask_wtf.csrf import validate_csrf
            try:
                validate_csrf(request.form.get('csrf_token'))
            except Exception as e:
                flash('CSRF token validation failed. Please try again.', 'error')
                return render_template('contact_us.html')

            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()

            # Basic validation
            if not all([name, email, subject, message]):
                flash('All fields are required.', 'error')
                return render_template('contact_us.html')

            # Email format validation
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                flash('Please enter a valid email address.', 'error')
                return render_template('contact_us.html')

            try:
                # Send email using Flask-Mail
                from flask_mail import Message
                from app import mail

                # Check if mail is properly configured
                if not mail or not app.config.get('MAIL_USERNAME'):
                    flash('Email service is not configured. Please contact us directly at simapan1996@gmail.com or call +91 62943 08077.', 'warning')
                    return render_template('contact_us.html')

                msg = Message(
                    subject=f"KitabGhar Contact: {subject}",
                    sender=app.config.get('MAIL_DEFAULT_SENDER', email),
                    recipients=[ADMIN_EMAIL],
                    reply_to=email,  # Allow admin to reply directly to user
                    body=f"""
New contact message from KitabGhar:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
Sent from KitabGhar Contact Form
This message was sent by: {name} ({email})
"""
                )
                mail.send(msg)
                flash('✅ Your message has been sent successfully.', 'success')
                return redirect(url_for('contact'))

            except Exception as e:
                app.logger.error(f"Email sending error: {str(e)}")
                error_msg = str(e).lower()

                # Provide specific error messages based on the error type
                if 'authentication' in error_msg or 'credentials' in error_msg or 'username and password not accepted' in error_msg:
                    app.logger.error("Gmail authentication failed - likely using regular password instead of App Password")
                    flash('❌ Email authentication failed. Please ensure you are using a Gmail App Password (not your regular password). Contact us directly at simapan1996@gmail.com or call +91 62943 08077.', 'error')
                elif 'connection' in error_msg or 'smtp' in error_msg:
                    flash('❌ Email server connection failed. Please try again later or contact us directly.', 'error')
                else:
                    flash('❌ Failed to send email. Please try again later or contact us directly.', 'error')

        return render_template('contact_us.html')
    except Exception as e:
        app.logger.error(f"Error rendering contact page: {str(e)}")
        return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/toggle_favorite/<book_id>', methods=['POST'])
@login_required
def toggle_favorite(book_id):
    """Toggle favorite status for a book"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login first', 'status': 'login_required'})

    try:
        # Try to convert to int for local books, keep as string for Google Books
        try:
            book_id_int = int(book_id)
            is_google_book = False
        except ValueError:
            # It's a Google Books ID (string)
            is_google_book = True

        if is_google_book:
            # For Google Books, just return a message that favorites are coming soon
            return jsonify({'success': False, 'message': 'Google Books favorites coming soon!', 'status': 'not_implemented'})

        # Handle local book favorites
        book = Ebook.query.get(book_id_int)
        if not book:
            return jsonify({'success': False, 'message': 'Book not found'})

        favorite = Favorite.query.filter_by(user_id=current_user.id, ebook_id=book_id_int).first()

        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({'success': True, 'favorited': False, 'message': 'Removed from favorites'})
        else:
            new_favorite = Favorite(user_id=current_user.id, ebook_id=book_id_int)
            db.session.add(new_favorite)
            db.session.commit()
            return jsonify({'success': True, 'favorited': True, 'message': 'Added to favorites'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred'})

@app.route('/save_google_book', methods=['POST'])
@login_required
def save_google_book():
    """Save a Google Books item to user's library"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Please login to save books', 'status': 'login_required'})

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400
    except Exception as e:
        app.logger.error(f"JSON parsing error: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400

    required_fields = ['google_books_id', 'title']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    # Check if already saved
    existing = SavedBook.query.filter_by(
        user_id=current_user.id,
        google_books_id=data['google_books_id']
    ).first()

    if existing:
        return jsonify({'success': False, 'message': 'Book already saved'})

    # Save the book
    saved_book = SavedBook(
        user_id=current_user.id,
        google_books_id=data['google_books_id'],
        title=data['title'],
        author=data.get('author'),
        thumbnail_url=data.get('thumbnail_url'),
        preview_link=data.get('preview_link'),
        published_year=data.get('published_year')
    )

    try:
        db.session.add(saved_book)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Book saved ✅'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving Google book: {str(e)}")
        return jsonify({'success': False, 'message': 'Error saving book'})

@app.route('/check_favorite/<int:book_id>')
@login_required
def check_favorite(book_id):
    """Check if a book is favorited by current user"""
    if not current_user.is_authenticated:
        return jsonify({'favorited': False, 'error': 'Authentication required'}), 401
    favorite = Favorite.query.filter_by(user_id=current_user.id, ebook_id=book_id).first()
    return jsonify({'favorited': favorite is not None})

@app.route('/favicon.ico')
def favicon():
    return send_file('static/images/logo.png', mimetype='image/png')
