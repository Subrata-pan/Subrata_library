# Dev and Deployment Guide

## Local Setup (Windows / PowerShell)

1. Create and activate a virtual environment
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies
```
pip install -r requirements.txt
```

3. Set environment variables (optional)
```
$env:FLASK_ENV="development"
$env:SESSION_SECRET="dev-secret-change"
# For Google OAuth (optional):
# $env:GOOGLE_CLIENT_ID="<your-client-id>"
# $env:GOOGLE_CLIENT_SECRET="<your-client-secret>"
```

4. Initialize database (first run)
```
python - <<'PY'
from app import app, db
with app.app_context():
    db.create_all()
print('DB initialized')
PY
```

5. Run the app
```
python main.py
```

Visit http://localhost:5000

## Free Hosting

- Render (recommended):
  - Create new Web Service → Connect repo
  - Build command: `pip install -r requirements.txt`
  - Start command: `gunicorn app:app`
  - Environment: set `PYTHON_VERSION` to your local Python (e.g. 3.11)
  - Add `DATABASE_URL` if using external DB. Default SQLite is fine for demos.

- Railway: Similar to Render. Start command `gunicorn app:app`.

## Features

- Advanced search & filters (author, category, language, date).
- Recommendations based on reading history.
- Reading progress sync + bookmarks.
- PDF reader with robust error handling and TTS option.
- "Recommended for You" sidebar while reading.
- Accessibility menu: font size, high-contrast, TTS toggle.
- Social sharing for quotes and progress.
- Google Sign-In optional.
- Premium responsive UI with lazy-loaded images and SEO meta.

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: Database ORM integration
- **SQLAlchemy**: Database abstraction layer with support for multiple database backends
- **Werkzeug**: WSGI utilities including secure filename handling and proxy fix middleware

### Frontend Dependencies
- **Bootstrap 5**: CSS framework via CDN for responsive design
- **Font Awesome 6**: Icon library via CDN for UI icons
- **Custom CSS/JS**: Application-specific styling and client-side functionality

### File Processing
- **Werkzeug Utils**: Secure filename processing for uploaded files
- **OS Module**: File system operations for upload directory management

### Database Support
- **SQLite**: Default development database (no additional setup required)
- **PostgreSQL**: Production database support via psycopg2 (when DATABASE_URL is configured)

### Configuration Management
- **Environment Variables**: 
  - DATABASE_URL for database connection
  - SESSION_SECRET for secure session management
- **Upload Configuration**: 50MB file size limit with PDF-only restriction