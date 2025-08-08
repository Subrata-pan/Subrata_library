from app import db
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
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    description = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who uploaded this book
    
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
    role = db.Column(db.String(20), nullable=False, default='Reader')  # Admin, Author, Reader
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
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
        return self.role == 'Admin'
    
    def is_author(self):
        """Check if user can upload books"""
        return self.role in ['Admin', 'Author']
    
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
