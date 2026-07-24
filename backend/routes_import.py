import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from google_books import fetch_cover
from models import Book, Highlight, ImportLog, db
from parser import content_hash, merge_notes_into_highlights, parse_clippings

import_bp = Blueprint("import_", __name__, url_prefix="/api")


@import_bp.post("/import")
@login_required
def import_clippings():
    if "file" not in request.files:
        return jsonify({"error": "no file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "no file selected"}), 400

    raw_bytes = file.read()
    try:
        raw_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("latin-1")

    user_dir = os.path.join(current_app.config["UPLOADS_DIR"], str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    safe_name = secure_filename(file.filename) or "My Clippings.txt"
    stored_name = f"{datetime.now(timezone.utc):%Y%m%d%H%M%S}_{safe_name}"
    with open(os.path.join(user_dir, stored_name), "w", encoding="utf-8") as fh:
        fh.write(raw_text)

    entries = parse_clippings(raw_text)
    entries = merge_notes_into_highlights(entries)

    book_cache = {}
    imported = 0
    duplicates = 0
    touched_books = set()

    for e in entries:
        book_key = (e["title"], e["author"])
        book = book_cache.get(book_key)
        if book is None:
            book = Book.query.filter_by(
                user_id=current_user.id, title=e["title"], author=e["author"]
            ).first()
            if book is None:
                cover_url, gb_id = None, None
                try:
                    cover_url, gb_id = fetch_cover(e["title"], e["author"])
                except Exception:
                    pass
                book = Book(
                    user_id=current_user.id,
                    title=e["title"],
                    author=e["author"],
                    cover_url=cover_url,
                    google_books_id=gb_id,
                )
                db.session.add(book)
                db.session.flush()
            book_cache[book_key] = book

        h_hash = content_hash(e["title"], e["author"], e["type"], e["location"], e["page"], e["text"])
        exists = Highlight.query.filter_by(user_id=current_user.id, content_hash=h_hash).first()
        if exists:
            duplicates += 1
            continue

        highlight = Highlight(
            user_id=current_user.id,
            book_id=book.id,
            type=e["type"],
            text=e["text"],
            note=e.get("note"),
            location=e["location"],
            page=e["page"],
            date_added=e["date_added"],
            content_hash=h_hash,
        )
        db.session.add(highlight)
        imported += 1
        touched_books.add(book.id)

        if e["date_added"] and (
            book.last_highlighted_at is None or e["date_added"] > book.last_highlighted_at
        ):
            book.last_highlighted_at = e["date_added"]

    log = ImportLog(
        user_id=current_user.id,
        filename=file.filename,
        imported_count=imported,
        duplicate_count=duplicates,
        book_count=len(touched_books),
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"log": log.to_dict()})


@import_bp.get("/import/logs")
@login_required
def import_logs():
    logs = (
        ImportLog.query.filter_by(user_id=current_user.id)
        .order_by(ImportLog.created_at.desc())
        .all()
    )
    return jsonify({"logs": [l.to_dict() for l in logs]})
