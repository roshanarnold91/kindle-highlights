import os

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "db", "highlights.db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOADS_DIR = UPLOADS_DIR
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB upload cap
    REMEMBER_COOKIE_DURATION_DAYS = int(os.environ.get("REMEMBER_COOKIE_DURATION_DAYS", "30"))
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")
    GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")
    APP_SMTP_SERVER = os.environ.get("APP_SMTP_SERVER", "")
    APP_SMTP_PORT = int(os.environ.get("APP_SMTP_PORT", "587"))
    APP_SMTP_EMAIL = os.environ.get("APP_SMTP_EMAIL", "")
    APP_SMTP_PASSWORD = os.environ.get("APP_SMTP_PASSWORD", "")
    APP_SMTP_USE_TLS = os.environ.get("APP_SMTP_USE_TLS", "true").lower() == "true"
    APP_SMTP_USE_SSL = os.environ.get("APP_SMTP_USE_SSL", "false").lower() == "true"
