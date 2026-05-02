#!/usr/bin/env python3
"""
Script to update existing books to have 'approved' status.
Run this once after deploying the new code to ensure all existing books are approved.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Ebook

def update_existing_books():
    """Update all existing books to have 'approved' status"""
    with app.app_context():
        try:
            # Update all books that don't have a status set (should be all existing books)
            books_updated = Ebook.query.filter(Ebook.status != 'approved').update({'status': 'approved'})
            db.session.commit()

            print(f"Successfully updated {books_updated} existing books to 'approved' status.")

            # Print statistics
            total_books = Ebook.query.count()
            approved_books = Ebook.query.filter_by(status='approved').count()
            pending_books = Ebook.query.filter_by(status='pending').count()
            rejected_books = Ebook.query.filter_by(status='rejected').count()

            print("\nBook Status Statistics:")
            print(f"   Total Books: {total_books}")
            print(f"   Approved: {approved_books}")
            print(f"   Pending: {pending_books}")
            print(f"   Rejected: {rejected_books}")

        except Exception as e:
            print(f"Error updating books: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    update_existing_books()
