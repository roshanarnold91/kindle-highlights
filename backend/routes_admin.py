import os

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from models import AdminSetting, Book, Highlight, ImportLog, User, db

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def admin_required():
    return current_user.is_authenticated and current_user.is_admin


@admin_bp.before_request
@login_required
def require_admin():
    if not admin_required():
        return jsonify({"error": "admin access required"}), 403


@admin_bp.get("/users")
def list_users():
    users = User.query.order_by(User.username).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@admin_bp.post("/users")
def create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or username).strip()

    if not username or len(password) < 8:
        return jsonify({"error": "username required and password must be at least 8 characters"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 409

    user = User(username=username, display_name=display_name, is_admin=bool(data.get("is_admin")))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user.to_dict()}), 201


@admin_bp.patch("/users/<int:user_id>")
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    data = request.get_json(silent=True) or {}
    if "disabled" in data:
        if user.id == current_user.id and data["disabled"]:
            return jsonify({"error": "cannot disable your own account"}), 400
        user.disabled = bool(data["disabled"])
    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])
    if "display_name" in data:
        user.display_name = (data["display_name"] or "").strip()[:120]
    if "new_password" in data and data["new_password"]:
        if len(data["new_password"]) < 8:
            return jsonify({"error": "password must be at least 8 characters"}), 400
        user.set_password(data["new_password"])

    db.session.commit()
    return jsonify({"user": user.to_dict()})


@admin_bp.delete("/users/<int:user_id>")
def delete_user(user_id):
    if user_id == current_user.id:
        return jsonify({"error": "cannot delete your own account"}), 400
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.get("/storage")
def storage_usage():
    users = User.query.all()
    usage = []
    for user in users:
        upload_dir = os.path.join(current_app.config["UPLOADS_DIR"], str(user.id))
        size = 0
        if os.path.isdir(upload_dir):
            for root, _dirs, files in os.walk(upload_dir):
                for f in files:
                    size += os.path.getsize(os.path.join(root, f))
        usage.append({
            "user_id": user.id,
            "username": user.username,
            "upload_bytes": size,
            "book_count": Book.query.filter_by(user_id=user.id).count(),
            "highlight_count": Highlight.query.filter_by(user_id=user.id).count(),
        })
    return jsonify({"usage": usage})


@admin_bp.get("/import-logs")
def all_import_logs():
    logs = (
        db.session.query(ImportLog, User.username)
        .join(User, ImportLog.user_id == User.id)
        .order_by(ImportLog.created_at.desc())
        .limit(200)
        .all()
    )
    return jsonify({
        "logs": [dict(l.to_dict(), username=username) for l, username in logs]
    })


@admin_bp.get("/smtp")
def get_app_smtp():
    keys = ["server", "port", "email", "use_tls", "use_ssl"]
    values = {k: AdminSetting.query.get(f"smtp_{k}") for k in keys}
    return jsonify({
        "smtp": {
            "server": values["server"].value if values["server"] else current_app.config["APP_SMTP_SERVER"],
            "port": int(values["port"].value) if values["port"] else current_app.config["APP_SMTP_PORT"],
            "email": values["email"].value if values["email"] else current_app.config["APP_SMTP_EMAIL"],
            "use_tls": (values["use_tls"].value == "true") if values["use_tls"] else current_app.config["APP_SMTP_USE_TLS"],
            "use_ssl": (values["use_ssl"].value == "true") if values["use_ssl"] else current_app.config["APP_SMTP_USE_SSL"],
            "password_set": bool(
                (AdminSetting.query.get("smtp_password") or AdminSetting()).value
                or current_app.config["APP_SMTP_PASSWORD"]
            ),
        }
    })


@admin_bp.put("/smtp")
def update_app_smtp():
    data = request.get_json(silent=True) or {}

    def set_setting(key, value):
        setting = AdminSetting.query.get(key)
        if setting is None:
            setting = AdminSetting(key=key)
            db.session.add(setting)
        setting.value = value

    if "server" in data:
        set_setting("smtp_server", data["server"] or "")
    if "port" in data:
        set_setting("smtp_port", str(data["port"] or 587))
    if "email" in data:
        set_setting("smtp_email", data["email"] or "")
    if "password" in data and data["password"]:
        set_setting("smtp_password", data["password"])
    if "use_tls" in data:
        set_setting("smtp_use_tls", "true" if data["use_tls"] else "false")
    if "use_ssl" in data:
        set_setting("smtp_use_ssl", "true" if data["use_ssl"] else "false")

    db.session.commit()
    return jsonify({"ok": True})
