import os
import tempfile
import pytest
from flask_testing import TestCase
from app import app, db
from models import User, Ebook
from flask_login import login_user, logout_user, current_user

class TestLogoutAndAdminApproval(TestCase):
    """Comprehensive tests for logout functionality and admin book approval system"""

    def create_app(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        import routes  # Ensure routes are registered
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()

        # Create admin user
        self.admin_user = User(
            username='admin',
            email='simapan1996@gmail.com',
            role='Admin',
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.set_password('admin123')

        # Create author user
        self.author_user = User(
            username='author',
            email='author@example.com',
            role='Author',
            first_name='Author',
            last_name='User'
        )
        self.author_user.set_password('author123')

        # Create regular reader user
        self.reader_user = User(
            username='reader',
            email='reader@example.com',
            role='Reader',
            first_name='Reader',
            last_name='User'
        )
        self.reader_user.set_password('reader123')

        db.session.add_all([self.admin_user, self.author_user, self.reader_user])
        db.session.commit()

        # Create a test PDF file
        self.test_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_book.pdf')
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%EOF')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)

    def login_admin(self):
        # Logout first if already logged in
        self.client.post('/auth/logout')
        return self.client.post('/auth/login', data={
            'username_or_email': 'simapan1996@gmail.com',
            'password': 'admin123'
        }, follow_redirects=True)

    def login_author(self):
        # Logout first if already logged in
        self.client.post('/auth/logout')
        return self.client.post('/auth/login', data={
            'username_or_email': 'author@example.com',
            'password': 'author123'
        }, follow_redirects=True)

    def login_reader(self):
        # Logout first if already logged in
        self.client.post('/auth/logout')
        return self.client.post('/auth/login', data={
            'username_or_email': 'reader@example.com',
            'password': 'reader123'
        }, follow_redirects=True)

    # Logout Functionality Tests
    def test_logout_clears_session_and_redirects(self):
        """Test that logout clears session and redirects properly"""
        self.login_author()
        response = self.client.post('/auth/logout', follow_redirects=True)
        self.assertIn(b'Goodbye', response.data)
        self.assertIn(b'Author User', response.data)  # User's name in message
        # After logout, user should not be authenticated
        with self.client:
            self.assertFalse(current_user.is_authenticated)

    def test_logout_redirects_to_homepage(self):
        """Test that logout redirects to homepage"""
        self.login_reader()
        response = self.client.post('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Check if we're on the home page (contains recent books or welcome message)
        self.assertIn(b'KitabGhar', response.data)

    def test_logout_requires_login(self):
        """Test that logout requires user to be logged in"""
        response = self.client.post('/auth/logout', follow_redirects=True)
        # Should redirect to login page
        self.assertIn(b'Please log in', response.data)

    def test_logout_clears_all_session_data(self):
        """Test that logout clears all session data"""
        with self.client:
            self.login_author()
            # Simulate some session data
            from flask import session
            session['test_key'] = 'test_value'
            self.assertIn('test_key', session)

            self.client.post('/auth/logout')
            # Session should be cleared
            self.assertNotIn('test_key', session)

    # Admin Dashboard Tests
    def test_admin_dashboard_accessible_only_by_admin(self):
        """Test that admin dashboard is accessible only by admin"""
        # Test with reader user
        self.login_reader()
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)
        self.assertIn(b'Admin privileges required', response.data)

        # Test with author user
        self.login_author()
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)

        # Test with admin user
        self.login_admin()
        response = self.client.get('/admin')
        self.assert200(response)
        self.assertIn(b'Admin Dashboard', response.data)

    def test_admin_dashboard_shows_pending_books_with_details(self):
        """Test that admin dashboard displays pending books with filename, download, and preview links"""
        self.login_author()
        # Upload a pending book
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Pending Book',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description for pending book',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)

        book = Ebook.query.filter_by(title='Pending Book').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.status, 'pending')

        self.login_admin()
        response = self.client.get('/admin')
        self.assert200(response)
        self.assertIn(b'Pending Book', response.data)
        self.assertIn(b'Test Author', response.data)
        self.assertIn(book.filename.encode(), response.data)
        self.assertIn(b'Download', response.data)
        self.assertIn(b'Preview', response.data)
        self.assertIn(b'Approve', response.data)
        self.assertIn(b'Reject', response.data)

    def test_admin_dashboard_shows_statistics(self):
        """Test that admin dashboard shows correct statistics"""
        # Create some books with different statuses
        pending_book = Ebook(
            title='Pending Book',
            author='Author',
            status='pending',
            file_path=self.test_pdf_path,
            filename='test.pdf',
            uploaded_by=self.author_user.id
        )
        approved_book = Ebook(
            title='Approved Book',
            author='Author',
            status='approved',
            file_path=self.test_pdf_path,
            filename='test2.pdf',
            uploaded_by=self.author_user.id
        )
        rejected_book = Ebook(
            title='Rejected Book',
            author='Author',
            status='rejected',
            file_path=self.test_pdf_path,
            filename='test3.pdf',
            uploaded_by=self.author_user.id
        )

        db.session.add_all([pending_book, approved_book, rejected_book])
        db.session.commit()

        self.login_admin()
        response = self.client.get('/admin')
        self.assert200(response)
        self.assertIn(b'1', response.data)  # Total pending
        self.assertIn(b'1', response.data)  # Total approved
        self.assertIn(b'1', response.data)  # Total rejected

    # Book Approval Tests
    def test_approve_book_updates_status_and_shows_message(self):
        """Test that approving a book updates status and shows success message"""
        self.login_author()
        # Upload a pending book
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Book to Approve',
                'author': 'Author',
                'category': 'Test',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)

        book = Ebook.query.filter_by(title='Book to Approve').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.status, 'pending')

        self.login_admin()
        # Approve the book (CSRF disabled in test environment)
        response = self.client.post(f'/admin/approve/{book.id}', follow_redirects=True)
        self.assertIn(b'approved and is now available', response.data)
        self.assertIn(b'Book to Approve', response.data)

        # Check database
        book = Ebook.query.get(book.id)
        self.assertEqual(book.status, 'approved')

    def test_reject_book_updates_status_and_shows_message(self):
        """Test that rejecting a book updates status and shows message"""
        self.login_author()
        # Upload a pending book
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Book to Reject',
                'author': 'Author',
                'category': 'Test',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)

        book = Ebook.query.filter_by(title='Book to Reject').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.status, 'pending')

        self.login_admin()
        # Reject the book
        response = self.client.post(f'/admin/reject/{book.id}', follow_redirects=True)
        self.assertIn(b'rejected', response.data)
        self.assertIn(b'Book to Reject', response.data)

        # Check database
        book = Ebook.query.get(book.id)
        self.assertEqual(book.status, 'rejected')

    def test_approve_reject_only_by_admin(self):
        """Test that only admin can approve/reject books"""
        self.login_author()
        # Upload a pending book
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Admin Only Book',
                'author': 'Author',
                'category': 'Test',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)

        book = Ebook.query.filter_by(title='Admin Only Book').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.status, 'pending')

        # Try to approve as author
        response = self.client.post(f'/admin/approve/{book.id}', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)
        book = Ebook.query.get(book.id)
        self.assertEqual(book.status, 'pending')  # Status unchanged

        # Try to reject as reader
        self.login_reader()
        response = self.client.post(f'/admin/reject/{book.id}', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)
        book = Ebook.query.get(book.id)
        self.assertEqual(book.status, 'pending')  # Status unchanged

    def test_approve_reject_non_pending_book_shows_warning(self):
        """Test approving/rejecting non-pending book shows warning"""
        # Create an approved book
        approved_book = Ebook(
            title='Already Approved',
            author='Author',
            status='approved',
            file_path=self.test_pdf_path,
            filename='approved.pdf',
            uploaded_by=self.author_user.id
        )
        db.session.add(approved_book)
        db.session.commit()

        self.login_admin()
        # Try to approve already approved book
        response = self.client.post(f'/admin/approve/{approved_book.id}', follow_redirects=True)
        self.assertIn(b'Book is not in pending status', response.data)

        # Try to reject already approved book
        response = self.client.post(f'/admin/reject/{approved_book.id}', follow_redirects=True)
        self.assertIn(b'Book is not in pending status', response.data)

    def test_approve_reject_invalid_book_id(self):
        """Test approving/rejecting with invalid book ID"""
        self.login_admin()
        response = self.client.post('/admin/approve/99999', follow_redirects=True)
        self.assert404(response)

        response = self.client.post('/admin/reject/99999', follow_redirects=True)
        self.assert404(response)

    # Upload Status Tests
    def test_upload_sets_book_status_to_pending(self):
        """Test that uploaded books have status 'pending'"""
        self.login_author()
        with open(self.test_pdf_path, 'rb') as f:
            response = self.client.post('/upload', data={
                'title': 'New Upload',
                'author': 'Test Author',
                'category': 'Fiction',
                'language': 'English',
                'description': 'A test book',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)

        book = Ebook.query.filter_by(title='New Upload').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.status, 'pending')

    # Unauthorized Access Tests
    def test_unauthenticated_user_cannot_access_admin_dashboard(self):
        """Test that unauthenticated users cannot access admin dashboard"""
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Please log in', response.data)

    def test_non_admin_cannot_access_protected_admin_routes(self):
        """Test that non-admin users cannot access admin-only routes"""
        self.login_reader()
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)

        # Test approve/reject routes
        response = self.client.post('/admin/approve/1', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)

        response = self.client.post('/admin/reject/1', follow_redirects=True)
        self.assertIn(b'Access denied', response.data)

    # Edge Cases
    def test_logout_when_not_logged_in(self):
        """Test logout behavior when user is not logged in"""
        response = self.client.post('/auth/logout', follow_redirects=True)
        # Should redirect to login or home
        self.assertIn(b'Please log in', response.data)

    def test_admin_dashboard_with_no_pending_books(self):
        """Test admin dashboard when there are no pending books"""
        self.login_admin()
        response = self.client.get('/admin')
        self.assert200(response)
        self.assertIn(b'0', response.data)  # No pending books

    def test_multiple_books_approval_workflow(self):
        """Test approving and rejecting multiple books"""
        self.login_author()
        # Upload multiple books
        books = []
        for i in range(3):
            with open(self.test_pdf_path, 'rb') as f:
                self.client.post('/upload', data={
                    'title': f'Book {i+1}',
                    'author': 'Author',
                    'category': 'Test',
                    'language': 'English',
                    'description': f'Description {i+1}',
                    'ebook': f
                }, content_type='multipart/form-data', follow_redirects=True)

            book = Ebook.query.filter_by(title=f'Book {i+1}').first()
            self.assertEqual(book.status, 'pending')
            books.append(book)

        self.login_admin()
        # Approve first book
        self.client.post(f'/admin/approve/{books[0].id}', follow_redirects=True)
        books[0] = Ebook.query.get(books[0].id)
        self.assertEqual(books[0].status, 'approved')

        # Reject second book
        self.client.post(f'/admin/reject/{books[1].id}', follow_redirects=True)
        books[1] = Ebook.query.get(books[1].id)
        self.assertEqual(books[1].status, 'rejected')

        # Third book remains pending
        books[2] = Ebook.query.get(books[2].id)
        self.assertEqual(books[2].status, 'pending')

    def test_logout_then_access_admin_requires_login(self):
        """Test that after logout, accessing /admin requires login again"""
        # Login as admin
        self.login_admin()
        # Verify admin can access dashboard
        response = self.client.get('/admin')
        self.assert200(response)
        self.assertIn(b'Admin Dashboard', response.data)

        # Logout
        self.client.post('/auth/logout', follow_redirects=True)

        # Try to access /admin after logout
        response = self.client.get('/admin', follow_redirects=True)
        # Should redirect to login page
        self.assertIn(b'Please log in', response.data)
        self.assertNotIn(b'Admin Dashboard', response.data)

if __name__ == '__main__':
    pytest.main([__file__])
