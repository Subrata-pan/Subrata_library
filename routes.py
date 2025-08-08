import os
from flask import render_template, request, redirect, url_for, flash, send_file, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func
from app import app, db
from models import Ebook, Category, User
from decorators import author_required, owns_book_or_admin

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Home page with recent uploads and statistics"""
    recent_books = Ebook.query.order_by(Ebook.upload_date.desc()).limit(5).all()
    total_books = Ebook.query.count()
    total_categories = Category.query.count()
    
    # Get category statistics
    category_stats = db.session.query(
        Ebook.category, 
        func.count(Ebook.id).label('count')
    ).group_by(Ebook.category).filter(Ebook.category.isnot(None)).all()
    
    return render_template('index.html', 
                         recent_books=recent_books,
                         total_books=total_books,
                         total_categories=total_categories,
                         category_stats=category_stats)

@app.route('/upload', methods=['GET', 'POST'])
@author_required
def upload():
    """Upload a new ebook"""
    if request.method == 'POST':
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
            
            # Save ebook info to database
            new_ebook = Ebook(
                title=title,
                author=author or None,
                category=category or None,
                language=language or None,
                file_path=filepath,
                filename=filename,
                file_size=file_size,
                description=description or None,
                uploaded_by=current_user.id
            )
            
            db.session.add(new_ebook)
            db.session.commit()
            
            flash(f"✅ '{title}' has been successfully uploaded!", 'success')
            return redirect(url_for('book_detail', id=new_ebook.id))
            
        except Exception as e:
            app.logger.error(f"Upload error: {str(e)}")
            flash('An error occurred while uploading the file. Please try again.', 'error')
            db.session.rollback()
    
    # Get existing categories for the dropdown
    categories = Category.query.order_by(Category.name).all()
    return render_template('upload.html', categories=categories)

@app.route('/browse')
def browse():
    """Browse all ebooks with search and filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    language_filter = request.args.get('language', '').strip()
    sort_by = request.args.get('sort', 'recent')  # recent, title, author
    
    # Base query
    query = Ebook.query
    
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
def book_detail(id):
    """Display detailed information about a specific book"""
    book = Ebook.query.get_or_404(id)
    return render_template('book_detail.html', book=book)

@app.route('/read/<int:id>')
def read_book(id):
    """Read a book online with PDF viewer"""
    book = Ebook.query.get_or_404(id)
    
    if not os.path.exists(book.file_path):
        flash('File not found on server!', 'error')
        return redirect(url_for('book_detail', id=id))
    
    return render_template('reader.html', book=book)

@app.route('/pdf/<int:id>')
def serve_pdf(id):
    """Serve PDF file for online reading"""
    book = Ebook.query.get_or_404(id)
    
    if not os.path.exists(book.file_path):
        abort(404)
    
    return send_file(book.file_path, 
                    mimetype='application/pdf')

@app.route('/download/<int:id>')
def download_book(id):
    """Download a specific book"""
    book = Ebook.query.get_or_404(id)
    
    if not os.path.exists(book.file_path):
        flash('File not found on server!', 'error')
        return redirect(url_for('book_detail', id=id))
    
    return send_file(book.file_path, 
                    as_attachment=True, 
                    download_name=f"{book.title}.pdf")

@app.route('/delete/<int:id>', methods=['POST'])
@owns_book_or_admin
def delete_book(id):
    """Delete a specific book"""
    book = Ebook.query.get_or_404(id)
    
    try:
        # Delete the file from filesystem
        if os.path.exists(book.file_path):
            os.remove(book.file_path)
        
        # Delete from database
        db.session.delete(book)
        db.session.commit()
        
        flash(f"'{book.title}' has been successfully deleted!", 'success')
        return redirect(url_for('browse'))
        
    except Exception as e:
        app.logger.error(f"Delete error: {str(e)}")
        flash('An error occurred while deleting the book.', 'error')
        db.session.rollback()
        return redirect(url_for('book_detail', id=id))

@app.route('/categories')
def categories():
    """List all categories"""
    categories = Category.query.order_by(Category.name).all()
    
    # Get book count for each category
    category_counts = {}
    for category in categories:
        count = Ebook.query.filter_by(category=category.name).count()
        category_counts[category.name] = count
    
    return render_template('categories.html', 
                         categories=categories,
                         category_counts=category_counts)

@app.route('/languages')
def languages():
    """List all available languages with book counts"""
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
    ).all()
    
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

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
