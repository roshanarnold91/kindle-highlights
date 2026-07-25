from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from email_service import (
    EmailError,
    send_book_email,
    send_selected_highlights_email,
    send_test_email,
)
from models import Book, Highlight, db

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

DISPLAY_PREFS = ("location", "page", "both", "neither")
HIGHLIGHT_TYPES = ("highlight", "note", "bookmark")


@settings_bp.get("")
@login_required
def get_settings():
    return jsonify({"user": current_user.to_dict(include_smtp=True)})


@settings_bp.put("")
@login_required
def update_settings():
    data = request.get_json(silent=True) or {}

    if "display_name" in data:
        current_user.display_name = (data["display_name"] or "").strip()[:120]

    if "display_pref" in data:
        if data["display_pref"] not in DISPLAY_PREFS:
            return jsonify({"error": "invalid display_pref"}), 400
        current_user.display_pref = data["display_pref"]

    if "theme" in data:
        if data["theme"] not in ("light", "dark", "sepia", "midnight", "system"):
            return jsonify({"error": "invalid theme"}), 400
        current_user.theme = data["theme"]

    if "status_count_types" in data:
        types = [t for t in (data["status_count_types"] or []) if t in HIGHLIGHT_TYPES]
        if not types:
            return jsonify({"error": "at least one type must count toward copy status"}), 400
        current_user.status_count_types = ",".join(types)

    if "smtp_server" in data:
        current_user.smtp_server = data["smtp_server"] or ""
    if "smtp_port" in data:
        current_user.smtp_port = int(data["smtp_port"] or 587)
    if "smtp_email" in data:
        current_user.smtp_email = data["smtp_email"] or ""
    if "smtp_password" in data and data["smtp_password"]:
        current_user.smtp_password = data["smtp_password"]
    if "smtp_use_tls" in data:
        current_user.smtp_use_tls = bool(data["smtp_use_tls"])
    if "smtp_use_ssl" in data:
        current_user.smtp_use_ssl = bool(data["smtp_use_ssl"])
    if "notify_email" in data:
        current_user.notify_email = (data["notify_email"] or "").strip()

    if "weekly_digest_enabled" in data:
        current_user.weekly_digest_enabled = bool(data["weekly_digest_enabled"])
    if "weekly_digest_day" in data:
        current_user.weekly_digest_day = int(data["weekly_digest_day"])
    if "weekly_digest_time" in data:
        current_user.weekly_digest_time = data["weekly_digest_time"]
    if "copy_notification_enabled" in data:
        current_user.copy_notification_enabled = bool(data["copy_notification_enabled"])

    db.session.commit()
    return jsonify({"user": current_user.to_dict(include_smtp=True)})


@settings_bp.post("/test-email")
@login_required
def test_email():
    try:
        to_addr = send_test_email(current_user)
    except EmailError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True, "sent_to": to_addr})


def _parse_email_override(data):
    to_addr = (data.get("to") or "").strip() or None
    if to_addr and "@" not in to_addr:
        return None, None, "please enter a valid email address"
    subject = (data.get("subject") or "").strip() or None
    return to_addr, subject, None


@settings_bp.post("/email/book/<int:book_id>")
@login_required
def email_book(book_id):
    book = Book.query.filter_by(id=book_id, user_id=current_user.id).first_or_404()
    highlights = (
        Highlight.query.filter_by(book_id=book.id, user_id=current_user.id)
        .order_by(Highlight.date_added.asc().nullslast())
        .all()
    )
    data = request.get_json(silent=True) or {}
    to_addr, subject, error = _parse_email_override(data)
    if error:
        return jsonify({"error": error}), 400
    try:
        send_book_email(current_user, book, highlights, to_addr=to_addr, subject=subject)
    except EmailError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True})


@settings_bp.post("/email/selected")
@login_required
def email_selected():
    data = request.get_json(silent=True) or {}
    ids = data.get("highlight_ids") or []
    if not ids:
        return jsonify({"error": "no highlights selected"}), 400

    highlights = Highlight.query.filter(
        Highlight.id.in_(ids), Highlight.user_id == current_user.id
    ).all()
    if not highlights:
        return jsonify({"error": "no matching highlights found"}), 404

    to_addr, subject, error = _parse_email_override(data)
    if error:
        return jsonify({"error": error}), 400

    book = Book.query.get(highlights[0].book_id)
    try:
        send_selected_highlights_email(current_user, book, highlights, to_addr=to_addr, subject=subject)
    except EmailError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True})
