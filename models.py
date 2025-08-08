from app import db
from datetime import datetime

class Ebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(200), nullable=True, index=True)
    category = db.Column(db.String(100), nullable=True, index=True)
    file_path = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
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

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'
