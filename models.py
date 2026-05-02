from extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Ebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(200), nullable=True, index=True)
    category = db.Column(db.String(100), nullable=True, index=True)
    language = db.Column(db.String(50), nullable=True, index=True)
    file_path = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    cover = db.Column(db.String(255), nullable=True)  # Cover image filename
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    description = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who uploaded this book
    status = db.Column(db.String(20), nullable=False, default='approved')  # pending, approved, rejected
    
    def __repr__(self):
        return f'<Ebook {self.title}>'
    
    def get_file_size_mb(self):
        """Return file size in MB formatted string"""
        if self.file_size:
            return f"{self.file_size / (1024*1024):.1f} MB"
        return "Unknown"
    
    def get_upload_date_formatted(self):
        """Return formatted upload date"""
        return self.upload_date.strftime("%B %d, %Y")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin, user
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)  # New field for profile image filename
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to books uploaded by this user (for Authors)
    uploaded_books = db.relationship('Ebook', backref='uploader', lazy=True, foreign_keys='Ebook.uploaded_by')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    def is_author(self):
        """Check if user can upload books"""
        return self.role in ['admin', 'user']
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def __repr__(self):
        return f'<User {self.username}({self.role})>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class ReadingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    ebook_id = db.Column(db.Integer, db.ForeignKey('ebook.id'), nullable=False, index=True)
    current_page = db.Column(db.Integer, nullable=False, default=1)
    total_pages = db.Column(db.Integer, nullable=True)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'ebook_id', name='uq_progress_user_book'),)

    user = db.relationship('User', backref=db.backref('reading_progress', lazy=True))
    ebook = db.relationship('Ebook', backref=db.backref('readers_progress', lazy=True))

    def progress_percent(self):
        if self.total_pages and self.total_pages > 0:
            return round((self.current_page / self.total_pages) * 100, 2)
        return None

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    ebook_id = db.Column(db.Integer, db.ForeignKey('ebook.id'), nullable=False, index=True)
    page = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('bookmarks', lazy=True))
    ebook = db.relationship('Ebook', backref=db.backref('bookmarks', lazy=True))

class ReadingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    ebook_id = db.Column(db.Integer, db.ForeignKey('ebook.id'), nullable=False, index=True)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('reading_history', lazy=True))
    ebook = db.relationship('Ebook', backref=db.backref('reading_history', lazy=True))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    ebook_id = db.Column(db.Integer, db.ForeignKey('ebook.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    ebook = db.relationship('Ebook', backref=db.backref('favorited_by', lazy=True))

    __table_args__ = (db.UniqueConstraint('user_id', 'ebook_id', name='uq_user_ebook_favorite'),)

    def __repr__(self):
        return f'<Favorite User {self.user_id} - Book {self.ebook_id}>'

class SavedBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    google_books_id = db.Column(db.String(255), nullable=False, index=True)  # Google Books API ID
    title = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(500), nullable=True)
    thumbnail_url = db.Column(db.String(1000), nullable=True)
    preview_link = db.Column(db.String(1000), nullable=True)
    published_year = db.Column(db.String(10), nullable=True)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('saved_books', lazy=True))

    __table_args__ = (db.UniqueConstraint('user_id', 'google_books_id', name='uq_user_google_book'),)

    def __repr__(self):
        return f'<SavedBook {self.title} by User {self.user_id}>'
