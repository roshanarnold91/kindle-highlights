import logging
import os
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from auth import auth_bp, init_login
from config import Config
from email_service import send_weekly_digest
from models import User, db
from routes_admin import admin_bp
from routes_books import books_bp
from routes_import import import_bp
from routes_settings import settings_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def create_app():
    app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
    app.config.from_object(Config)

    os.makedirs(os.path.dirname(app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")), exist_ok=True)
    os.makedirs(app.config["UPLOADS_DIR"], exist_ok=True)

    db.init_app(app)
    init_login(app)
    CORS(app, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        bootstrap_admin(app)

    register_static_routes(app)
    start_scheduler(app)

    return app


def bootstrap_admin(app):
    if User.query.filter_by(is_admin=True).first():
        return
    username = app.config["ADMIN_USERNAME"]
    existing = User.query.filter_by(username=username).first()
    if existing:
        existing.is_admin = True
        db.session.commit()
        return
    admin = User(username=username, display_name="Administrator", is_admin=True)
    admin.set_password(app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()
    logger.info("Bootstrapped admin account '%s'", username)


def register_static_routes(app):
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def spa_fallback(_error):
        if os.path.exists(os.path.join(STATIC_DIR, "index.html")):
            return send_from_directory(STATIC_DIR, "index.html")
        return jsonify({"error": "not found"}), 404


def start_scheduler(app):
    scheduler = BackgroundScheduler(daemon=True)

    def run_digest_job():
        with app.app_context():
            now = datetime.now(timezone.utc)
            users = User.query.filter_by(weekly_digest_enabled=True, disabled=False).all()
            for user in users:
                try:
                    hour, minute = (int(x) for x in (user.weekly_digest_time or "08:00").split(":"))
                except ValueError:
                    hour, minute = 8, 0
                if now.weekday() != user.weekly_digest_day:
                    continue
                if now.hour != hour:
                    continue
                if user.last_digest_sent_at and (now - user.last_digest_sent_at).total_seconds() < 6 * 3600:
                    continue
                try:
                    sent = send_weekly_digest(user)
                    if sent:
                        user.last_digest_sent_at = now
                        db.session.commit()
                except Exception:
                    logger.exception("Failed to send weekly digest to %s", user.username)

    scheduler.add_job(run_digest_job, "interval", minutes=60, id="weekly_digest", replace_existing=True)
    scheduler.start()


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
