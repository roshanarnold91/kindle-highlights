import io
import zipfile
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

import google_books
import open_library
from formatting import (
    effective_pref,
    format_book_highlights,
    format_book_highlights_html,
    format_book_highlights_pdf,
    wrap_html_document,
)
from models import Book, CopyHistory, Highlight, db
from pdf_export import html_to_pdf_bytes

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


@books_bp.get("/books/<int:book_id>/metadata-search")
@login_required
def metadata_search(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    query = (request.args.get("q") or "").strip() or f"{book.title} {book.author}".strip()

    results = []
    try:
        results += google_books.search_metadata(query, max_results=5)
    except Exception:
        pass
    try:
        results += open_library.search_metadata(query, max_results=5)
    except Exception:
        pass

    return jsonify({"results": results})


@books_bp.post("/books/<int:book_id>/metadata-match")
@login_required
def metadata_match(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}

    book.cover_url = data.get("cover_url")
    book.description = data.get("description")
    book.publisher = data.get("publisher")
    book.published_date = data.get("published_date")
    book.metadata_source = data.get("source") or "manual"
    book.google_books_id = data.get("source_id") if data.get("source") == "google" else None

    db.session.commit()
    return jsonify({"book": book.to_dict()})


def _filtered_highlights_query(book, args):
    q = Highlight.query.filter_by(book_id=book.id, user_id=current_user.id)

    types = [t for t in args.getlist("type") if t in ("highlight", "note", "bookmark")]
    if types:
        q = q.filter(Highlight.type.in_(types))

    copied = args.get("copied")
    if copied == "true":
        q = q.filter(Highlight.copied_at.isnot(None))
    elif copied == "false":
        q = q.filter(Highlight.copied_at.is_(None))

    date_from = args.get("date_from")
    date_to = args.get("date_to")
    if date_from:
        q = q.filter(Highlight.date_added >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(Highlight.date_added <= datetime.fromisoformat(date_to))

    search = (args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        q = q.filter(db.or_(Highlight.text.ilike(like), Highlight.note.ilike(like)))

    return q


@books_bp.get("/books/<int:book_id>/highlights")
@login_required
def list_highlights(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    q = _filtered_highlights_query(book, request.args)
    highlights = q.order_by(Highlight.date_added.asc().nullslast()).all()
    return jsonify({
        "book": book.to_dict(),
        "highlights": [h.to_dict() for h in highlights],
        "display_pref": effective_pref(current_user, book),
    })


def _safe_filename(title):
    return "".join(c for c in title if c.isalnum() or c in " -_").strip() or "highlights"


@books_bp.get("/books/<int:book_id>/export")
@login_required
def export_highlights(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    q = _filtered_highlights_query(book, request.args)
    highlights = q.order_by(Highlight.date_added.asc().nullslast()).all()

    safe_name = _safe_filename(book.title)
    fmt = request.args.get("format", "pdf")

    if fmt == "html":
        body_html = format_book_highlights_html(book, highlights, current_user)
        doc = wrap_html_document(book.title, body_html)
        response = current_app.response_class(doc, mimetype="text/html")
        response.headers["Content-Disposition"] = f'attachment; filename="{safe_name}.html"'
        return response

    body_html = format_book_highlights_pdf(book, highlights, current_user)
    doc = wrap_html_document(book.title, body_html)
    pdf_bytes = html_to_pdf_bytes(doc)
    response = current_app.response_class(pdf_bytes, mimetype="application/pdf")
    response.headers["Content-Disposition"] = f'attachment; filename="{safe_name}.pdf"'
    return response


@books_bp.post("/books/export-bulk")
@login_required
def export_bulk():
    data = request.get_json(silent=True) or {}
    ids = data.get("book_ids") or []
    if not ids:
        return jsonify({"error": "no books selected"}), 400

    books_by_id = {
        b.id: b for b in Book.query.filter(Book.id.in_(ids), Book.user_id == current_user.id).all()
    }
    if not books_by_id:
        return jsonify({"error": "no matching books found"}), 404

    buf = io.BytesIO()
    used_names = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for book_id in ids:
            book = books_by_id.get(book_id)
            if not book:
                continue
            highlights = (
                Highlight.query.filter_by(book_id=book.id, user_id=current_user.id)
                .order_by(Highlight.date_added.asc().nullslast())
                .all()
            )
            body_html = format_book_highlights_pdf(book, highlights, current_user)
            doc = wrap_html_document(book.title, body_html)
            pdf_bytes = html_to_pdf_bytes(doc)

            base_name = _safe_filename(book.title)
            name, n = f"{base_name}.pdf", 2
            while name in used_names:
                name = f"{base_name} ({n}).pdf"
                n += 1
            used_names.add(name)
            zf.writestr(name, pdf_bytes)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    response = current_app.response_class(buf.getvalue(), mimetype="application/zip")
    response.headers["Content-Disposition"] = f'attachment; filename="highlights-export-{timestamp}.zip"'
    return response


@books_bp.post("/books/<int:book_id>/copy")
@login_required
def copy_book(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "all")  # all | new
    types = [t for t in (data.get("types") or []) if t in ("highlight", "note", "bookmark")]

    q = Highlight.query.filter_by(book_id=book.id, user_id=current_user.id)
    if mode == "new":
        q = q.filter(Highlight.copied_at.is_(None))
    if types:
        q = q.filter(Highlight.type.in_(types))
    highlights = q.order_by(Highlight.date_added.asc().nullslast()).all()

    text = format_book_highlights(book, highlights, current_user)
    html = format_book_highlights_html(book, highlights, current_user)

    now = datetime.now(timezone.utc)
    for h in highlights:
        h.copied_at = now
    book.last_copied_at = now

    history = CopyHistory(user_id=current_user.id, book_id=book.id, copy_type=mode)
    history.set_ids([h.id for h in highlights])
    db.session.add(history)
    db.session.commit()

    return jsonify({"text": text, "html": html, "count": len(highlights)})


@books_bp.post("/books/<int:book_id>/copy/reset")
@login_required
def reset_copy_status(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    highlights = Highlight.query.filter_by(book_id=book.id, user_id=current_user.id).all()

    for h in highlights:
        h.copied_at = None
    book.last_copied_at = None

    history = CopyHistory(user_id=current_user.id, book_id=book.id, copy_type="reset")
    history.set_ids([h.id for h in highlights])
    db.session.add(history)
    db.session.commit()

    return jsonify({"book": book.to_dict()})


@books_bp.post("/highlights/<int:highlight_id>/copy")
@login_required
def copy_highlight(highlight_id):
    highlight = Highlight.query.filter_by(id=highlight_id, user_id=current_user.id).first_or_404()
    book = Book.query.get(highlight.book_id)
    text = format_book_highlights(book, [highlight], current_user)
    html = format_book_highlights_html(book, [highlight], current_user)

    now = datetime.now(timezone.utc)
    highlight.copied_at = now
    book.last_copied_at = now

    history = CopyHistory(user_id=current_user.id, book_id=book.id, copy_type="individual")
    history.set_ids([highlight.id])
    db.session.add(history)
    db.session.commit()

    return jsonify({"text": text, "html": html, "count": 1})
