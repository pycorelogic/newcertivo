import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))


def _bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"true", "1", "yes", "on"}


def _default_site_url() -> str:
    explicit = os.environ.get("SITE_URL")
    if explicit:
        return explicit

    vercel_url = os.environ.get("VERCEL_URL")
    if vercel_url:
        return f"https://{vercel_url}"

    return "http://localhost:5000"


def _database_uri() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            return db_url.replace("postgres://", "postgresql://", 1)
        return db_url

    return f"sqlite:///{os.path.join(ROOT_DIR, 'database.db')}"


class Config:
    IS_VERCEL = bool(os.environ.get("VERCEL"))

    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or "dev-secret-key-change-in-production-immediately"
    )
    DEBUG = False
    TESTING = False

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, "static", "uploads")
    )
    UPLOADS_ENABLED = _bool_env("UPLOADS_ENABLED", default=not IS_VERCEL)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@certivo.com")
    MAIL_MAX_EMAILS = 10
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@certivo.com")

    POSTS_PER_PAGE = 9
    COMMENTS_PER_PAGE = 20
    ADMIN_ITEMS_PER_PAGE = 20

    SITE_NAME = os.environ.get("SITE_NAME", "Certivo")
    SITE_TAGLINE = os.environ.get("SITE_TAGLINE", "Insights, Ideas & Innovation")
    SITE_URL = _default_site_url()
    SITE_DESCRIPTION = os.environ.get(
        "SITE_DESCRIPTION",
        "A modern blog covering technology, business, lifestyle and travel.",
    )
    SITE_AUTHOR = os.environ.get("SITE_AUTHOR", "Certivo Team")
    SITE_TWITTER = os.environ.get("SITE_TWITTER", "@certivo")
    SITE_LOGO = os.environ.get("SITE_LOGO", "")

    ADSENSE_CLIENT_ID = os.environ.get("ADSENSE_CLIENT_ID", "ca-pub-XXXXXXXXXXXXXXXXX")
    ADSENSE_ENABLED = os.environ.get("ADSENSE_ENABLED", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    GA_TRACKING_ID = os.environ.get("GA_TRACKING_ID", "")

    SCSS_INPUT = os.path.join(BASE_DIR, "static", "scss", "main.scss")
    SCSS_OUTPUT = os.path.join(BASE_DIR, "static", "css", "main.css")
    SCSS_LOAD_PATHS = [os.path.join(BASE_DIR, "static", "scss")]
    COMPILE_SCSS_ON_BOOT = _bool_env("COMPILE_SCSS_ON_BOOT", default=not IS_VERCEL)

    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=12)
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "logs/certivo.log")
    LOG_TO_STDOUT = _bool_env("LOG_TO_STDOUT", default=IS_VERCEL)


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECRET_KEY = os.environ.get("SECRET_KEY") or (_ for _ in ()).throw(
        RuntimeError("Set the SECRET_KEY environment variable in production!")
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "default")
    return config_map.get(env, DevelopmentConfig)
