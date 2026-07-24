import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

from formatting import format_book_highlights

logger = logging.getLogger(__name__)


class EmailError(Exception):
    pass


def _app_fallback_smtp():
    from models import AdminSetting

    def get(key, default=""):
        setting = AdminSetting.query.get(key)
        return setting.value if setting else default

    cfg = current_app.config
    server = get("smtp_server") or cfg.get("APP_SMTP_SERVER")
    email = get("smtp_email") or cfg.get("APP_SMTP_EMAIL")
    if not server or not email:
        return None
    port_raw = get("smtp_port")
    return {
        "server": server,
        "port": int(port_raw) if port_raw else cfg.get("APP_SMTP_PORT", 587),
        "email": email,
        "password": get("smtp_password") or cfg.get("APP_SMTP_PASSWORD"),
        "use_tls": (get("smtp_use_tls") == "true") if get("smtp_use_tls") else cfg.get("APP_SMTP_USE_TLS", True),
    }


def _resolve_smtp(user, use_app_fallback=True):
    if user.smtp_server and user.smtp_email and user.smtp_password:
        return {
            "server": user.smtp_server,
            "port": user.smtp_port or 587,
            "email": user.smtp_email,
            "password": user.smtp_password,
            "use_tls": user.smtp_use_tls,
        }
    if use_app_fallback:
        return _app_fallback_smtp()
    return None


def send_email(user, subject, body, to_addr=None):
    smtp_cfg = _resolve_smtp(user)
    if not smtp_cfg:
        raise EmailError("No SMTP configuration available (per-user or app fallback).")

    to_addr = to_addr or user.notify_email or user.smtp_email or smtp_cfg["email"]

    msg = MIMEMultipart()
    msg["From"] = smtp_cfg["email"]
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_cfg["server"], smtp_cfg["port"], timeout=15) as server:
            if smtp_cfg["use_tls"]:
                server.starttls()
            server.login(smtp_cfg["email"], smtp_cfg["password"])
            server.sendmail(smtp_cfg["email"], [to_addr], msg.as_string())
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailError(str(exc)) from exc

    return to_addr


def send_test_email(user):
    return send_email(
        user,
        subject="Kindle Highlights Manager — Test Email",
        body="This is a test email from Kindle Highlights Manager. Your SMTP settings are working.",
    )


def send_book_email(user, book, highlights):
    body = format_book_highlights(book, highlights, user)
    subject = f"Highlights: {book.title}"
    send_email(user, subject, body)


def send_selected_highlights_email(user, book, highlights):
    body = format_book_highlights(book, highlights, user)
    subject = f"Selected highlights from {book.title}"
    send_email(user, subject, body)


def send_copy_notification(user, book, count):
    if not user.copy_notification_enabled:
        return
    body = f"{count} highlight(s) from '{book.title}' were copied to your clipboard."
    send_email(user, subject=f"Copied highlights: {book.title}", body=body)


def send_weekly_digest(user):
    from models import Book, Highlight

    since = user.last_digest_sent_at or (datetime.now(timezone.utc) - timedelta(days=7))
    new_highlights = (
        Highlight.query.filter(Highlight.user_id == user.id, Highlight.created_at >= since)
        .order_by(Highlight.book_id, Highlight.date_added)
        .all()
    )
    if not new_highlights:
        return False

    by_book = {}
    for h in new_highlights:
        by_book.setdefault(h.book_id, []).append(h)

    sections = []
    for book_id, hls in by_book.items():
        book = Book.query.get(book_id)
        if not book:
            continue
        sections.append(format_book_highlights(book, hls, user))

    body = f"Weekly digest — {len(new_highlights)} new highlight(s) across {len(by_book)} book(s)\n\n"
    body += ("\n\n" + ("=" * 40) + "\n\n").join(sections)

    send_email(user, subject="Kindle Highlights — Weekly Digest", body=body)
    return True
