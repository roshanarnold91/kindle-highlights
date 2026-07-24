from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from models import User, db

login_manager = LoginManager()
login_manager.session_protection = "strong"

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "authentication required"}), 401


def init_login(app):
    login_manager.init_app(app)

    @app.before_request
    def set_remember_duration():
        current_app.permanent_session_lifetime = timedelta(
            days=current_app.config["REMEMBER_COOKIE_DURATION_DAYS"]
        )


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    remember = bool(data.get("remember"))

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid username or password"}), 401
    if user.disabled:
        return jsonify({"error": "account disabled"}), 403

    login_user(user, remember=remember)
    return jsonify({"user": user.to_dict()})


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"user": None})
    return jsonify({"user": current_user.to_dict()})


@auth_bp.post("/change-password")
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not current_user.check_password(current_password):
        return jsonify({"error": "current password is incorrect"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "new password must be at least 8 characters"}), 400

    current_user.set_password(new_password)
    db.session.commit()
    return jsonify({"ok": True})
