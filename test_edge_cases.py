import os
import pytest
from flask_testing import TestCase
from app import app, db
from models import User, Ebook


class TestEdgeCases(TestCase):
    """Test edge cases and error scenarios"""

    def create_app(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test-secret-key'
        return app

    def setUp(self):
        db.create_all()

        # Create admin user
        self.admin_user = User(
            username='admin',
            email='simapan1996@gmail.com',
            role='Admin'
        )
        self.admin_user.set_password('admin123')
        db.session.add(self.admin_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_approve_nonexistent_book(self):
        """Test approving a book that doesn't exist."""
        from flask_login import login_user

        with self.client:
            login_user(self.admin_user)
            response = self.client.post('/admin/approve/999')
            self.assert404(response)

    def test_reject_nonexistent_book(self):
        """Test rejecting a book that doesn't exist."""
        from flask_login import login_user

        with self.client:
            login_user(self.admin_user)
            response = self.client.post('/admin/reject/999')
            self.assert404(response)

    def test_download_nonexistent_book(self):
        """Test downloading a book that doesn't exist."""
        from flask_login import login_user

        with self.client:
            login_user(self.admin_user)
            response = self.client.get('/download/999')
            self.assert404(response)

    def test_read_nonexistent_book(self):
        """Test reading a book that doesn't exist."""
        from flask_login import login_user

        with self.client:
            login_user(self.admin_user)
            response = self.client.get('/read/999')
            self.assert404(response)

    def test_approve_already_approved_book(self):
        """Test approving a book that's already approved."""
        from flask_login import login_user

        # Create an approved book
        book = Ebook(
            title='Already Approved',
            author='Test',
            file_path='/fake/path.pdf',
            filename='test.pdf',
            file_size=1024,
            status='approved'
        )
        db.session.add(book)
        db.session.commit()

        with self.client:
            login_user(self.admin_user)
            response = self.client.post(f'/admin/approve/{book.id}', follow_redirects=True)
            # Check flash message
            self.assertIn(b'Book is not in pending status', response.data)

    def test_reject_already_rejected_book(self):
        """Test rejecting a book that's already rejected."""
        from flask_login import login_user

        # Create a rejected book
        book = Ebook(
            title='Already Rejected',
            author='Test',
            file_path='/fake/path.pdf',
            filename='test.pdf',
            file_size=1024,
            status='rejected'
        )
        db.session.add(book)
        db.session.commit()

        with self.client:
            login_user(self.admin_user)
            response = self.client.post(f'/admin/reject/{book.id}', follow_redirects=True)
            # Check flash message
            self.assertIn(b'Book is not in pending status', response.data)


if __name__ == '__main__':
    pytest.main([__file__])
