# KitabGhar User Management Script

This script provides command-line tools for managing users in the KitabGhar database using argparse.

## Usage

```bash
python manage_users.py <command> [options]
```

## Available Commands

### 1. Delete User
Delete a user from the database by email address.

```bash
python manage_users.py delete_user --email user@example.com
```

**Options:**
- `--email`: Email address of the user to delete (required)
- `--confirm`: Skip confirmation prompt (optional)

**Example:**
```bash
# With confirmation prompt
python manage_users.py delete_user --email test@example.com

# Skip confirmation (use with caution!)
python manage_users.py delete_user --email test@example.com --confirm
```

### 2. List Users
List all users in the database with their details.

```bash
python manage_users.py list_users
```

### 3. Create Admin
Create a new admin user if one doesn't already exist with the specified email.

```bash
python manage_users.py create_admin --username admin --email admin@example.com --password securepass
```

**Options:**
- `--username`: Username for the admin (required)
- `--email`: Email address for the admin (required)
- `--password`: Password for the admin (required)
- `--first-name`: First name (optional)
- `--last-name`: Last name (optional)

## Examples

```bash
# List all users
python manage_users.py list_users

# Delete a user (with confirmation)
python manage_users.py delete_user --email test@example.com

# Delete a user without confirmation
python manage_users.py delete_user --email test@example.com --confirm

# Create a new admin user
python manage_users.py create_admin --username superadmin --email admin@kitabghar.com --password mysecurepass --first-name Super --last-name Admin
```

## Safety Features

- **Confirmation Prompts**: The delete command asks for confirmation before proceeding
- **Error Handling**: Proper error messages for missing users or database issues
- **Transaction Safety**: Uses database transactions with rollback on errors
- **Duplicate Prevention**: Create admin checks if user already exists
- **Case-Insensitive**: Email matching is case-insensitive

## Requirements

- Python 3.x
- Flask and SQLAlchemy (already included in requirements.txt)

## Database

The script automatically connects to the same database used by the Flask application:
- Default: `instance/kitabghar.db`
- Can be overridden with `DATABASE_URL` environment variable

## Notes

- The script imports the same models and database configuration as the main Flask app
- All operations are performed within a Flask application context
- User deletion is permanent and cannot be undone
- Admin creation will fail if an admin with the same email already exists
- Make sure to backup your database before performing delete operations
