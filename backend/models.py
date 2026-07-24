import json
from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


DISPLAY_PREFS = ("location", "page", "both", "neither")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=False, default="")
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    disabled = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Display preferences
    display_pref = db.Column(db.String(20), default="both", nullable=False)
    theme = db.Column(db.String(10), default="system", nullable=False)  # light/dark/system

    # Comma-separated subset of highlight/note/bookmark that counts toward a
    # book's "copied" status (none/partial/full).
    status_count_types = db.Column(db.String(50), default="highlight,note,bookmark", nullable=False)

    # SMTP settings (per user)
    smtp_server = db.Column(db.String(255), default="")
    smtp_port = db.Column(db.Integer, default=587)
    smtp_email = db.Column(db.String(255), default="")
    smtp_password = db.Column(db.String(255), default="")
    smtp_use_tls = db.Column(db.Boolean, default=True)
    # Where highlight emails/digests are delivered. Falls back to smtp_email
    # (the sending account) when unset, so existing "email myself" setups
    # keep working unchanged.
    notify_email = db.Column(db.String(255), default="")

    # Digest / notification prefs
    weekly_digest_enabled = db.Column(db.Boolean, default=False)
    weekly_digest_day = db.Column(db.Integer, default=0)  # 0=Monday ... 6=Sunday
    weekly_digest_time = db.Column(db.String(5), default="08:00")  # HH:MM
    copy_notification_enabled = db.Column(db.Boolean, default=False)
    last_digest_sent_at = db.Column(db.DateTime, nullable=True)

    books = db.relationship("Book", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    highlights = db.relationship("Highlight", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    import_logs = db.relationship("ImportLog", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    copy_history = db.relationship("CopyHistory", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_smtp=False):
        data = {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "is_admin": self.is_admin,
            "disabled": self.disabled,
            "display_pref": self.display_pref,
            "theme": self.theme,
            "status_count_types": self.status_count_types.split(",") if self.status_count_types else [],
            "weekly_digest_enabled": self.weekly_digest_enabled,
            "weekly_digest_day": self.weekly_digest_day,
            "weekly_digest_time": self.weekly_digest_time,
            "copy_notification_enabled": self.copy_notification_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_smtp:
            data.update({
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "smtp_email": self.smtp_email,
                "smtp_use_tls": self.smtp_use_tls,
                "smtp_password_set": bool(self.smtp_password),
                "notify_email": self.notify_email,
            })
        return data


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(300), default="")
    cover_url = db.Column(db.String(500), nullable=True)
    google_books_id = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    publisher = db.Column(db.String(255), nullable=True)
    published_date = db.Column(db.String(20), nullable=True)
    metadata_source = db.Column(db.String(20), nullable=True)  # google/openlibrary/manual
    display_pref_override = db.Column(db.String(20), nullable=True)  # None = use user default
    created_at = db.Column(db.DateTime, default=utcnow)
    last_highlighted_at = db.Column(db.DateTime, default=utcnow)
    last_copied_at = db.Column(db.DateTime, nullable=True)

    highlights = db.relationship("Highlight", backref="book", cascade="all, delete-orphan", lazy="dynamic")

    __table_args__ = (db.UniqueConstraint("user_id", "title", "author", name="uq_user_book"),)

    def to_dict(self):
        total = self.highlights.count()
        copied = self.highlights.filter(Highlight.copied_at.isnot(None)).count()

        status_types = (self.user.status_count_types or "highlight,note,bookmark").split(",")
        status_q = self.highlights.filter(Highlight.type.in_(status_types))
        status_total = status_q.count()
        status_copied = status_q.filter(Highlight.copied_at.isnot(None)).count()
        if status_total == 0:
            copy_status = "none"
        elif status_copied == 0:
            copy_status = "none"
        elif status_copied == status_total:
            copy_status = "full"
        else:
            copy_status = "partial"

        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "cover_url": self.cover_url,
            "description": self.description,
            "publisher": self.publisher,
            "published_date": self.published_date,
            "metadata_source": self.metadata_source,
            "display_pref_override": self.display_pref_override,
            "highlight_count": self.highlights.filter_by(type="highlight").count(),
            "note_count": self.highlights.filter_by(type="note").count(),
            "bookmark_count": self.highlights.filter_by(type="bookmark").count(),
            "total_count": total,
            "copied_count": copied,
            "copy_status": copy_status,
            "last_highlighted_at": self.last_highlighted_at.isoformat() if self.last_highlighted_at else None,
            "last_copied_at": self.last_copied_at.isoformat() if self.last_copied_at else None,
        }


class Highlight(db.Model):
    __tablename__ = "highlights"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="highlight")  # highlight/note/bookmark
    text = db.Column(db.Text, default="")
    note = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(50), nullable=True)
    page = db.Column(db.String(50), nullable=True)
    date_added = db.Column(db.DateTime, nullable=True)
    content_hash = db.Column(db.String(64), nullable=False, index=True)
    copied_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "content_hash", name="uq_user_highlight_hash"),)

    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "type": self.type,
            "text": self.text,
            "note": self.note,
            "location": self.location,
            "page": self.page,
            "date_added": self.date_added.isoformat() if self.date_added else None,
            "copied_at": self.copied_at.isoformat() if self.copied_at else None,
        }


class ImportLog(db.Model):
    __tablename__ = "import_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    imported_count = db.Column(db.Integer, default=0)
    duplicate_count = db.Column(db.Integer, default=0)
    book_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "imported_count": self.imported_count,
            "duplicate_count": self.duplicate_count,
            "book_count": self.book_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CopyHistory(db.Model):
    __tablename__ = "copy_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    highlight_ids = db.Column(db.Text, default="[]")  # JSON list
    copy_type = db.Column(db.String(20), default="all")  # all/new/individual
    created_at = db.Column(db.DateTime, default=utcnow)

    def set_ids(self, ids):
        self.highlight_ids = json.dumps(ids)

    def get_ids(self):
        return json.loads(self.highlight_ids or "[]")


class AdminSetting(db.Model):
    __tablename__ = "admin_settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, default="")
