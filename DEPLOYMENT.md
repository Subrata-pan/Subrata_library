# Kitab Ghar Deployment

## Recommended Host: Render

This app is ready for Render using the included `render.yaml`.

1. Push the repository to GitHub.
2. In Render, choose **New > Blueprint**.
3. Connect the GitHub repo.
4. Render will create:
   - a Python web service
   - a PostgreSQL database
   - a generated `SESSION_SECRET`

## Required Environment Variables

Set these in the Render service dashboard:

```text
ADMIN_EMAIL=your_admin_email@example.com
ADMIN_PASSWORD=use_a_strong_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
```

Optional Google sign-in/search variables:

```text
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_BOOKS_API_KEY=
```

## Build And Start Commands

Render should read these automatically from `render.yaml`.

```text
Build command: pip install -r requirements.txt
Start command: gunicorn app:app
```

## Important Notes

- Do not deploy `.env`, local SQLite databases, `__pycache__`, or local upload folders.
- Rotate any real secret that was ever committed to git before deploying.
- Render's free web service filesystem is temporary, so user-uploaded PDFs can disappear after restarts. For production uploads, move files to object storage such as S3, Cloudinary, or Supabase Storage.
