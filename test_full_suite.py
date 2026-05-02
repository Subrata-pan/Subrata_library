import os
import tempfile
import pytest
from flask_testing import TestCase
from app import app, db
from models import User, Ebook
from flask_login import login_user, logout_user, current_user

class TestKitabGharFullSuite(TestCase):
    """Comprehensive test suite for KitabGhar Flask application"""

    def create_app(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test-secret-key'
        app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        import routes  # Ensure routes are registered
        import auth
        import services
        # Blueprints are already registered in app.py, so we don't need to register them again
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()

        # Helper to generate unique email
        import random
        import string
        def unique_email(base):
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            return f"{base}_{suffix}@example.com"

        # Create admin user
        self.admin_user = User(
            username='admin',
            email='simapan1996@gmail.com',
            role='Admin',
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.set_password('admin123')

        # Create regular user
        self.regular_user = User(
            username='testuser',
            email=unique_email('testuser'),
            role='Reader',
            first_name='Test',
            last_name='User'
        )
        self.regular_user.set_password('test123')

        # Create author user
        self.author_user = User(
            username='author',
            email=unique_email('author'),
            role='Author',
            first_name='Author',
            last_name='User'
        )
        self.author_user.set_password('author123')

        db.session.add_all([self.admin_user, self.regular_user, self.author_user])
        db.session.commit()

        # Create a test PDF file
        self.test_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_book.pdf')
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)

    # Helper login methods
    def login_admin(self):
        return self.client.post('/auth/login', data={
            'username_or_email': 'simapan1996@gmail.com',
            'password': 'admin123'
        }, follow_redirects=True)

    def login_regular_user(self):
        return self.client.post('/auth/login', data={
            'username_or_email': self.regular_user.email,
            'password': 'test123'
        }, follow_redirects=True)

    def login_author(self):
        return self.client.post('/auth/login', data={
            'username_or_email': self.author_user.email,
            'password': 'author123'
        }, follow_redirects=True)

    # 1. User Authentication Tests
    def test_register_unique_email(self):
        response = self.client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'unique@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Registration successful', response.data)

        # Logout after successful registration
        self.client.get('/auth/logout')

        # Attempt duplicate email registration
        response_dup = self.client.post('/auth/register', data={
            'username': 'newuser2',
            'email': 'unique@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Email already registered', response_dup.data)

    def test_login_valid_credentials(self):
        response = self.login_regular_user()
        self.assert200(response)
        self.assertIn(b'Welcome', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post('/auth/login', data={
            'username_or_email': 'wronguser',
            'password': 'wrongpass'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username/email or password', response.data)

    def test_logout_clears_session(self):
        self.login_regular_user()
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertIn(b'Login', response.data)

    # 2. Book Upload & Approval Flow
    def test_upload_book_pending_status(self):
        self.login_author()
        with open(self.test_pdf_path, 'rb') as f:
            response = self.client.post('/upload', data={
                'title': 'Test Book',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b'has been successfully uploaded', response.data)
        book = Ebook.query.filter_by(title='Test Book').first()
        self.assertIsNotNone(book)
        self.assertEqual(book.status, 'pending')

    def test_book_not_visible_until_approved(self):
        self.login_author()
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Hidden Book',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)
        self.login_regular_user()
        response = self.client.get('/')
        self.assertNotIn(b'Hidden Book', response.data)

    def test_admin_approves_book(self):
        self.login_author()
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Approve Book',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)
        book = Ebook.query.filter_by(title='Approve Book').first()
        # Logout author and login admin
        self.client.get('/auth/logout')
        self.login_admin()
        response = self.client.post(f'/admin/approve/{book.id}', follow_redirects=True)
        self.assertIn(b'has been approved and is now available in the library', response.data)
        book = Ebook.query.get(book.id)
        self.assertEqual(book.status, 'approved')

    def test_admin_rejects_book(self):
        self.login_author()
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Reject Book',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)
        book = Ebook.query.filter_by(title='Reject Book').first()
        # Logout author and login admin
        self.client.get('/auth/logout')
        self.login_admin()
        response = self.client.post(f'/admin/reject/{book.id}', follow_redirects=True)
        self.assertIn(b'has been rejected', response.data)
        book = Ebook.query.get(book.id)
        self.assertEqual(book.status, 'rejected')

    # 3. Access Control
    def test_admin_access_control(self):
        self.login_regular_user()
        response = self.client.get('/admin', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        # Accept both relative and absolute URLs for redirect location
        self.assertIn(response.location, ['/', 'http://localhost/'])
        # Logout regular user and login admin
        self.client.get('/auth/logout')
        self.login_admin()
        response = self.client.get('/admin', follow_redirects=True)
        self.assert200(response)
        self.assertIn(b'Admin Dashboard', response.data)

    def test_non_logged_in_redirects(self):
        protected_routes = ['/upload', '/admin', '/auth/profile']
        for route in protected_routes:
            response = self.client.get(route, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/auth/login', response.location)

    # 4. Book Actions
    def test_preview_and_download_approved_book(self):
        self.login_author()
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'PreviewDownload Book',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)
        book = Ebook.query.filter_by(title='PreviewDownload Book').first()
        # Create the actual file at the book's file_path
        with open(book.file_path, 'wb') as f:
            f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF')
        self.login_admin()
        self.client.post(f'/admin/approve/{book.id}', follow_redirects=True)
        self.client.get('/auth/logout')  # Logout admin
        self.login_regular_user()  # Login regular user
        response_preview = self.client.get(f'/read/{book.id}')
        self.assert200(response_preview)
        self.assertIn(b'PreviewDownload Book', response_preview.data)
        response_download = self.client.get(f'/download/{book.id}')
        self.assert200(response_download)
        self.assertEqual(response_download.headers['Content-Type'], 'application/pdf')

    def test_rejected_books_not_listed(self):
        self.login_author()
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Rejected Book',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)
        book = Ebook.query.filter_by(title='Rejected Book').first()
        self.login_admin()
        self.client.post(f'/admin/reject/{book.id}', follow_redirects=True)
        self.login_regular_user()
        response = self.client.get('/')
        self.assertNotIn(b'Rejected Book', response.data)

    # 5. Edge Cases
    def test_duplicate_email_registration(self):
        response = self.client.post('/auth/register', data={
            'username': 'dupuser',
            'email': 'dup@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful', response.data)

        # Logout after successful registration
        self.client.get('/auth/logout')

        response_dup = self.client.post('/auth/register', data={
            'username': 'dupuser2',
            'email': 'dup@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Email already registered', response_dup.data)

    def test_upload_invalid_file_type(self):
        self.login_author()
        with open(__file__, 'rb') as f:  # Upload this python file as invalid type
            response = self.client.post('/upload', data={
                'title': 'Invalid File',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b'Only PDF files are allowed', response.data)

    def test_download_pending_or_rejected_book(self):
        self.login_author()
        with open(self.test_pdf_path, 'rb') as f:
            self.client.post('/upload', data={
                'title': 'Pending Book',
                'author': 'Test Author',
                'category': 'Test Category',
                'language': 'English',
                'description': 'Test description',
                'ebook': f
            }, content_type='multipart/form-data', follow_redirects=True)
        book = Ebook.query.filter_by(title='Pending Book').first()
        self.login_regular_user()
        response = self.client.get(f'/download/{book.id}', follow_redirects=False)
        self.assertEqual(response.status_code, 302)  # Redirect to home

        self.login_admin()
        self.client.post(f'/admin/reject/{book.id}', follow_redirects=True)
        self.login_regular_user()
        response_reject = self.client.get(f'/download/{book.id}', follow_redirects=False)
        self.assertEqual(response_reject.status_code, 302)  # Redirect to home

if __name__ == '__main__':
    pytest.main([__file__])
