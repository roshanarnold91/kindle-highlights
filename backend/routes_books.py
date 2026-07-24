from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from formatting import effective_pref, format_book_highlights
from models import Book, CopyHistory, Highlight, db

books_bp = Blueprint("books", __name__, url_prefix="/api")


@books_bp.get("/books")
@login_required
def list_books():
    q = Book.query.filter_by(user_id=current_user.id)

    search = (request.args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        q = q.filter(db.or_(Book.title.ilike(like), Book.author.ilike(like)))

    status = request.args.get("status", "all")
    books = q.all()
    results = [b.to_dict() for b in books]

    if status == "never_copied":
        results = [b for b in results if b["copy_status"] == "none"]
    elif status == "partially_copied":
        results = [b for b in results if b["copy_status"] == "partial"]
    elif status == "fully_copied":
        results = [b for b in results if b["copy_status"] == "full"]

    sort = request.args.get("sort", "recent")
    if sort == "title":
        results.sort(key=lambda b: b["title"].lower())
    elif sort == "author":
        results.sort(key=lambda b: (b["author"] or "").lower())
    elif sort == "most_highlights":
        results.sort(key=lambda b: b["total_count"], reverse=True)
    else:
        results.sort(key=lambda b: b["last_highlighted_at"] or "", reverse=True)

    return jsonify({"books": results})


@books_bp.get("/books/<int:book_id>")
@login_required
def get_book(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    return jsonify({"book": book.to_dict()})


@books_bp.patch("/books/<int:book_id>")
@login_required
def update_book(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}
    if "display_pref_override" in data:
        val = data["display_pref_override"]
        if val not in (None, "location", "page", "both", "neither"):
            return jsonify({"error": "invalid display_pref_override"}), 400
        book.display_pref_override = val
    db.session.commit()
    return jsonify({"book": book.to_dict()})


@books_bp.get("/books/<int:book_id>/highlights")
@login_required
def list_highlights(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    q = Highlight.query.filter_by(book_id=book.id, user_id=current_user.id)

    htype = request.args.get("type")
    if htype in ("highlight", "note", "bookmark"):
        q = q.filter_by(type=htype)

    copied = request.args.get("copied")
    if copied == "true":
        q = q.filter(Highlight.copied_at.isnot(None))
    elif copied == "false":
        q = q.filter(Highlight.copied_at.is_(None))

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        q = q.filter(Highlight.date_added >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(Highlight.date_added <= datetime.fromisoformat(date_to))

    search = (request.args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        q = q.filter(db.or_(Highlight.text.ilike(like), Highlight.note.ilike(like)))

    highlights = q.order_by(Highlight.date_added.asc().nullslast()).all()
    return jsonify({
        "book": book.to_dict(),
        "highlights": [h.to_dict() for h in highlights],
        "display_pref": effective_pref(current_user, book),
    })


@books_bp.post("/books/<int:book_id>/copy")
@login_required
def copy_book(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "all")  # all | new

    q = Highlight.query.filter_by(book_id=book.id, user_id=current_user.id)
    if mode == "new":
        q = q.filter(Highlight.copied_at.is_(None))
    highlights = q.order_by(Highlight.date_added.asc().nullslast()).all()

    text = format_book_highlights(book, highlights, current_user)

    now = datetime.now(timezone.utc)
    for h in highlights:
        h.copied_at = now
    book.last_copied_at = now

    history = CopyHistory(user_id=current_user.id, book_id=book.id, copy_type=mode)
    history.set_ids([h.id for h in highlights])
    db.session.add(history)
    db.session.commit()

    return jsonify({"text": text, "count": len(highlights)})


@books_bp.post("/highlights/<int:highlight_id>/copy")
@login_required
def copy_highlight(highlight_id):
    highlight = Highlight.query.filter_by(id=highlight_id, user_id=current_user.id).first_or_404()
    book = Book.query.get(highlight.book_id)
    text = format_book_highlights(book, [highlight], current_user)

    now = datetime.now(timezone.utc)
    highlight.copied_at = now
    book.last_copied_at = now

    history = CopyHistory(user_id=current_user.id, book_id=book.id, copy_type="individual")
    history.set_ids([highlight.id])
    db.session.add(history)
    db.session.commit()

    return jsonify({"text": text, "count": 1})
