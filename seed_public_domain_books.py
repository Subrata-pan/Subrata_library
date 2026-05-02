import argparse
import os
import re
import textwrap
from datetime import datetime

import requests
from werkzeug.utils import secure_filename

from app import app
from extensions import db
from models import Category, Ebook, User


BOOKS = [
    {"id": 1342, "title": "Pride and Prejudice", "author": "Jane Austen", "category": "Classic Fiction", "language": "English"},
    {"id": 84, "title": "Frankenstein", "author": "Mary Wollstonecraft Shelley", "category": "Horror", "language": "English"},
    {"id": 1661, "title": "The Adventures of Sherlock Holmes", "author": "Arthur Conan Doyle", "category": "Mystery", "language": "English"},
    {"id": 11, "title": "Alice's Adventures in Wonderland", "author": "Lewis Carroll", "category": "Fantasy", "language": "English"},
    {"id": 2701, "title": "Moby-Dick", "author": "Herman Melville", "category": "Classic Fiction", "language": "English"},
    {"id": 98, "title": "A Tale of Two Cities", "author": "Charles Dickens", "category": "Historical Fiction", "language": "English"},
    {"id": 74, "title": "The Adventures of Tom Sawyer", "author": "Mark Twain", "category": "Adventure", "language": "English"},
    {"id": 76, "title": "Adventures of Huckleberry Finn", "author": "Mark Twain", "category": "Adventure", "language": "English"},
    {"id": 1400, "title": "Great Expectations", "author": "Charles Dickens", "category": "Classic Fiction", "language": "English"},
    {"id": 345, "title": "Dracula", "author": "Bram Stoker", "category": "Horror", "language": "English"},
    {"id": 1080, "title": "A Modest Proposal", "author": "Jonathan Swift", "category": "Essay", "language": "English"},
    {"id": 1952, "title": "The Yellow Wallpaper", "author": "Charlotte Perkins Gilman", "category": "Short Story", "language": "English"},
    {"id": 64317, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "category": "Classic Fiction", "language": "English"},
    {"id": 2542, "title": "A Doll's House", "author": "Henrik Ibsen", "category": "Drama", "language": "English"},
    {"id": 1260, "title": "Jane Eyre", "author": "Charlotte Bronte", "category": "Classic Fiction", "language": "English"},
    {"id": 2554, "title": "Crime and Punishment", "author": "Fyodor Dostoyevsky", "category": "Classic Fiction", "language": "English"},
    {"id": 2600, "title": "War and Peace", "author": "Leo Tolstoy", "category": "Classic Fiction", "language": "English"},
    {"id": 8800, "title": "The Divine Comedy", "author": "Dante Alighieri", "category": "Poetry", "language": "English"},
    {"id": 4300, "title": "Ulysses", "author": "James Joyce", "category": "Classic Fiction", "language": "English"},
    {"id": 5200, "title": "Metamorphosis", "author": "Franz Kafka", "category": "Classic Fiction", "language": "English"},
    {"id": 174, "title": "The Picture of Dorian Gray", "author": "Oscar Wilde", "category": "Classic Fiction", "language": "English"},
    {"id": 41, "title": "The Legend of Sleepy Hollow", "author": "Washington Irving", "category": "Horror", "language": "English"},
    {"id": 1232, "title": "The Prince", "author": "Niccolo Machiavelli", "category": "Philosophy", "language": "English"},
    {"id": 1497, "title": "The Republic", "author": "Plato", "category": "Philosophy", "language": "English"},
]


def gutenberg_text_urls(book_id):
    return [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
    ]


def clean_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    start_match = re.search(r"\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*?\*\*\*", text, re.IGNORECASE | re.DOTALL)
    end_match = re.search(r"\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .*?\*\*\*", text, re.IGNORECASE | re.DOTALL)
    if start_match and end_match and start_match.end() < end_match.start():
        text = text[start_match.end():end_match.start()]
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def download_text(book):
    last_error = None
    headers = {"User-Agent": "KitabGhar public-domain library seeder"}
    for url in gutenberg_text_urls(book["id"]):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            if response.text.strip():
                return clean_text(response.text), url
        except requests.RequestException as exc:
            last_error = exc
    raise RuntimeError(f"Could not download {book['title']}: {last_error}")


def pdf_string(value):
    value = value.encode("latin-1", "replace").decode("latin-1")
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_simple_pdf(path, title, author, body):
    lines = [title, f"by {author}", "", ""]
    for paragraph in body.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=86, replace_whitespace=False) or [""])

    lines_per_page = 44
    pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
    objects = []

    def add_object(content):
        objects.append(content)
        return len(objects)

    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids = []
    for page_lines in pages:
        y = 760
        text_ops = ["BT", "/F1 10 Tf", "50 760 Td", "14 TL"]
        first = True
        for line in page_lines:
            if first:
                text_ops.append(f"({pdf_string(line)}) Tj")
                first = False
            else:
                text_ops.append(f"T* ({pdf_string(line)}) Tj")
            y -= 14
            if y < 40:
                break
        text_ops.append("ET")
        stream = "\n".join(text_ops)
        content_id = add_object(f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream")
        page_id = add_object(f"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>")
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    pages_id = add_object(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>")
    catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

    objects = [obj.replace("/Parent 0 0 R", f"/Parent {pages_id} 0 R") for obj in objects]
    offsets = []
    pdf = bytearray(b"%PDF-1.4\n")
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n{obj}\nendobj\n".encode("latin-1"))

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1"))

    with open(path, "wb") as pdf_file:
        pdf_file.write(pdf)


def ensure_category(name):
    category = Category.query.filter_by(name=name).first()
    if category:
        return category
    category = Category(name=name)
    db.session.add(category)
    return category


def seed_books(limit=None, force=False):
    upload_dir = app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    admin = User.query.filter_by(role="admin").first()
    imported = 0
    skipped = 0
    failed = []

    for book in BOOKS[:limit]:
        existing = Ebook.query.filter_by(title=book["title"], author=book["author"]).first()
        if existing and not force:
            skipped += 1
            print(f"Skipped: {book['title']} already exists")
            continue

        print(f"Downloading: {book['title']}")
        try:
            text, source_url = download_text(book)
        except RuntimeError as exc:
            failed.append((book["title"], str(exc)))
            print(f"Failed: {book['title']} ({exc})")
            continue
        filename = secure_filename(f"{book['title']}_{book['id']}.pdf")
        file_path = os.path.join(upload_dir, filename)
        write_simple_pdf(file_path, book["title"], book["author"], text)

        ensure_category(book["category"])
        if existing and force:
            ebook = existing
        else:
            ebook = Ebook(title=book["title"], author=book["author"])
            db.session.add(ebook)

        ebook.category = book["category"]
        ebook.language = book["language"]
        ebook.file_path = file_path
        ebook.filename = filename
        ebook.file_size = os.path.getsize(file_path)
        ebook.cover = None
        ebook.description = f"Public-domain text from Project Gutenberg. Source: {source_url}"
        ebook.uploaded_by = admin.id if admin else None
        ebook.status = "approved"
        ebook.upload_date = datetime.utcnow()
        imported += 1
        db.session.commit()
        print(f"Added: {book['title']}")

    return imported, skipped, failed


def main():
    parser = argparse.ArgumentParser(description="Seed KitabGhar with public-domain books.")
    parser.add_argument("--limit", type=int, default=None, help="Only import the first N books.")
    parser.add_argument("--force", action="store_true", help="Update existing matching book records.")
    args = parser.parse_args()

    with app.app_context():
        imported, skipped, failed = seed_books(limit=args.limit, force=args.force)
        print(f"Done. Imported/updated: {imported}. Skipped: {skipped}.")
        if failed:
            print("Failed downloads:")
            for title, error in failed:
                print(f"- {title}: {error}")


if __name__ == "__main__":
    main()
