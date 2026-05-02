import os

import requests
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from extensions import db
from models import Ebook, ReadingProgress, Bookmark, ReadingHistory

api = Blueprint('api', __name__)


@api.route('/google-books/search')
@login_required
def google_books_search():
    query = (request.args.get('q') or '').strip()
    if not query:
        return jsonify({'items': [], 'message': 'Please enter a book name to search.'}), 400

    params = {
        'q': query,
        'maxResults': min(request.args.get('max_results', default=12, type=int), 20),
        'printType': 'books',
    }
    api_key = os.environ.get('GOOGLE_BOOKS_API_KEY')
    if api_key:
        params['key'] = api_key

    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get('https://www.googleapis.com/books/v1/volumes', params=params, timeout=8)
        response.raise_for_status()
    except requests.RequestException:
        fallback_books = search_open_library(query, params['maxResults'])
        if fallback_books:
            return jsonify({
                'items': fallback_books,
                'source': 'open_library',
                'message': 'Google Books is unavailable, showing fallback book results.'
            })
        return jsonify({'items': [], 'message': 'Google Books search is unavailable right now. Add GOOGLE_BOOKS_API_KEY in .env if this continues.'}), 502

    books = []
    for item in response.json().get('items', []):
        volume = item.get('volumeInfo', {})
        image_links = volume.get('imageLinks') or {}
        thumbnail = image_links.get('thumbnail') or image_links.get('smallThumbnail') or ''
        if thumbnail.startswith('http://'):
            thumbnail = 'https://' + thumbnail[len('http://'):]

        books.append({
            'id': item.get('id'),
            'title': volume.get('title') or 'Unknown Title',
            'authors': ', '.join(volume.get('authors') or []) or 'Unknown Author',
            'published_year': (volume.get('publishedDate') or 'Unknown Year')[:4],
            'thumbnail': thumbnail,
            'preview_link': volume.get('previewLink') or volume.get('infoLink') or '',
        })

    return jsonify({'items': books, 'source': 'google_books'})


def search_open_library(query, limit):
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get(
            'https://openlibrary.org/search.json',
            params={'q': query, 'limit': limit},
            timeout=8
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    books = []
    for item in response.json().get('docs', []):
        cover_id = item.get('cover_i')
        thumbnail = f'https://covers.openlibrary.org/b/id/{cover_id}-M.jpg' if cover_id else ''
        open_library_key = item.get('key') or ''
        preview_link = f'https://openlibrary.org{open_library_key}' if open_library_key else ''
        books.append({
            'id': item.get('key') or item.get('edition_key', [''])[0],
            'title': item.get('title') or 'Unknown Title',
            'authors': ', '.join(item.get('author_name') or []) or 'Unknown Author',
            'published_year': str(item.get('first_publish_year') or 'Unknown Year'),
            'thumbnail': thumbnail,
            'preview_link': preview_link,
            'source': 'open_library',
        })

    return books


@api.route('/progress', methods=['POST'])
@login_required
def save_progress():
    data = request.get_json(force=True)
    ebook_id = int(data.get('ebook_id'))
    current_page = int(data.get('current_page', 1))
    total_pages = int(data.get('total_pages', 0)) or None

    progress = ReadingProgress.query.filter_by(user_id=current_user.id, ebook_id=ebook_id).first()
    if not progress:
        progress = ReadingProgress(user_id=current_user.id, ebook_id=ebook_id)
        db.session.add(progress)
    progress.current_page = current_page
    progress.total_pages = total_pages or progress.total_pages
    db.session.commit()
    return jsonify({'status': 'ok'})


@api.route('/progress/<int:ebook_id>', methods=['GET'])
@login_required
def get_progress(ebook_id: int):
    progress = ReadingProgress.query.filter_by(user_id=current_user.id, ebook_id=ebook_id).first()
    if not progress:
        return jsonify({}), 200
    return jsonify({
        'ebook_id': ebook_id,
        'current_page': progress.current_page,
        'total_pages': progress.total_pages,
        'last_read_at': progress.last_read_at.isoformat() if progress.last_read_at else None
    })


@api.route('/bookmarks', methods=['POST'])
@login_required
def add_bookmark():
    data = request.get_json(force=True)
    ebook_id = int(data.get('ebook_id'))
    page = int(data.get('page'))
    note = (data.get('note') or '').strip() or None
    bm = Bookmark(user_id=current_user.id, ebook_id=ebook_id, page=page, note=note)
    db.session.add(bm)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': bm.id})


@api.route('/bookmarks/<int:ebook_id>', methods=['GET'])
@login_required
def list_bookmarks(ebook_id: int):
    bms = Bookmark.query.filter_by(user_id=current_user.id, ebook_id=ebook_id).order_by(Bookmark.page.asc()).all()
    return jsonify([{'id': b.id, 'page': b.page, 'note': b.note, 'created_at': b.created_at.isoformat()} for b in bms])


@api.route('/recommendations')
@login_required
def recommendations():
    # Simple heuristic: find books in same categories or by same authors that user read recently
    recent = db.session.query(ReadingHistory.ebook_id).filter(ReadingHistory.user_id == current_user.id).order_by(ReadingHistory.accessed_at.desc()).limit(20).subquery()
    base_books = Ebook.query.filter(Ebook.id.in_(recent)).all()
    like_cats = [b.category for b in base_books if b.category]
    like_authors = [b.author for b in base_books if b.author]

    query = Ebook.query
    filters = []
    if like_cats:
        filters.append(Ebook.category.in_(like_cats))
    if like_authors:
        filters.append(Ebook.author.in_(like_authors))
    if filters:
        query = query.filter(or_(*filters))
    ebook_id = request.args.get('ebook_id', type=int)
    if ebook_id:
        query = query.filter(Ebook.id != ebook_id)
    items = query.order_by(Ebook.upload_date.desc()).limit(12).all()
    return jsonify([{'id': b.id, 'title': b.title, 'author': b.author, 'category': b.category} for b in items])


