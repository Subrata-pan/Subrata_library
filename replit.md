# KitabGhar - Digital Library Management System

## Overview

KitabGhar is a Flask-based digital library management system designed for uploading, organizing, and accessing PDF ebooks. The application provides a clean web interface for users to manage their personal digital book collection with features including file uploads, categorization, search functionality, and detailed book management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses a server-side rendered approach with Flask templates and Bootstrap for responsive UI design. The frontend consists of:

- **Template Engine**: Jinja2 templates with a base template inheritance pattern
- **UI Framework**: Bootstrap 5 with dark theme for consistent styling
- **Icons**: Font Awesome for visual elements
- **JavaScript**: Vanilla JavaScript for client-side interactions including form validation, tooltips, and auto-dismissing alerts
- **Responsive Design**: Mobile-first approach with responsive grid layouts

### Backend Architecture
Built on Flask with a modular structure separating concerns:

- **Web Framework**: Flask with SQLAlchemy ORM for database operations
- **Database Layer**: SQLAlchemy with SQLite as default database, configurable via environment variables
- **File Handling**: Secure file uploads with validation, stored in local uploads directory
- **Session Management**: Flask sessions with configurable secret key
- **Middleware**: ProxyFix for handling reverse proxy headers
- **Logging**: Built-in Python logging for debugging and monitoring

### Data Storage
The application uses a relational database approach with two main entities:

- **Ebook Model**: Stores book metadata including title, author, category, file information, upload dates, and descriptions
- **Category Model**: Manages book categories with descriptions and creation dates
- **File Storage**: Physical PDF files stored in local filesystem with secure filename handling
- **Database Configuration**: Supports both SQLite (development) and PostgreSQL (production) via DATABASE_URL environment variable

### Key Design Patterns
- **MVC Pattern**: Clear separation between models (data), views (templates), and controllers (routes)
- **Factory Pattern**: Database and application initialization with proper context management
- **Repository Pattern**: SQLAlchemy ORM abstracts database operations
- **Template Inheritance**: Base template with block-based content sections for consistency

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