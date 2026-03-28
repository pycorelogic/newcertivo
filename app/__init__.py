import json
import logging
import os
from datetime import datetime

import sass
from flask import Flask
from flask_login import current_user

from app.config import get_config
from app.extensions import csrf, db, limiter, login_manager, mail, migrate

logger = logging.getLogger(__name__)


def create_app(config_class=None):
    """Application factory to create and configure the Flask app."""

    app = Flask(__name__, instance_relative_config=False)

    cfg = config_class or get_config()
    app.config.from_object(cfg)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    from app.routes.admin import bp as admin_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.blog import bp as blog_bp
    from app.routes.main import bp as main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    _register_jinja_helpers(app)

    if app.config.get("COMPILE_SCSS_ON_BOOT", True):
        _compile_scss(app)

    upload_folder = app.config.get("UPLOAD_FOLDER", "")
    if upload_folder and app.config.get("UPLOADS_ENABLED", True):
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(os.path.join(upload_folder, "posts"), exist_ok=True)
        os.makedirs(os.path.join(upload_folder, "editor"), exist_ok=True)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com "
            "https://pagead2.googlesyndication.com https://www.google-analytics.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://www.google-analytics.com;"
        )
        response.headers["Content-Security-Policy"] = csp
        return response

    with app.app_context():
        db.create_all()

    if not app.debug:
        handler = _build_log_handler(app)
        handler.setFormatter(
            logging.Formatter(
                app.config.get(
                    "LOG_FORMAT",
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]",
                )
            )
        )
        handler.setLevel(app.config.get("LOG_LEVEL", "INFO"))

        app.logger.addHandler(handler)
        app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))
        app.logger.info("Certivo Blog startup")

    return app


def _build_log_handler(app: Flask) -> logging.Handler:
    if app.config.get("LOG_TO_STDOUT", False):
        return logging.StreamHandler()

    from logging.handlers import RotatingFileHandler

    log_file = app.config.get("LOG_FILE", "logs/certivo.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    return RotatingFileHandler(log_file, maxBytes=10240000, backupCount=5)


def _register_jinja_helpers(app: Flask) -> None:
    """Register custom Jinja2 filters, tests, and global functions."""

    from app.utils.helpers import (
        auto_excerpt,
        human_date,
        human_datetime,
        strip_html,
        time_ago,
        truncate,
    )

    app.jinja_env.filters["time_ago"] = time_ago
    app.jinja_env.filters["human_date"] = human_date
    app.jinja_env.filters["human_datetime"] = human_datetime
    app.jinja_env.filters["strip_html"] = strip_html
    app.jinja_env.filters["truncate_words"] = truncate
    app.jinja_env.filters["auto_excerpt"] = auto_excerpt

    @app.template_filter("hex_to_rgb")
    def hex_to_rgb_filter(value: str) -> tuple[int, int, int]:
        if not value or not isinstance(value, str):
            return (0, 0, 0)
        value = value.lstrip("#")
        try:
            if len(value) == 3:
                value = "".join([c * 2 for c in value])
            return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return (0, 0, 0)

    @app.template_filter("is_light")
    def is_light_filter(rgb: tuple[int, int, int]) -> bool:
        if not rgb or len(rgb) != 3:
            return False
        r, g, b = rgb
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance > 0.6

    @app.template_filter("filesize")
    def filesize_filter(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @app.template_filter("format_number")
    def format_number_filter(value: int) -> str:
        if value is None:
            return "0"
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)

    @app.template_filter("tojson_pretty")
    def tojson_pretty_filter(value) -> str:
        return json.dumps(value, indent=2, ensure_ascii=False)

    app.jinja_env.globals["now"] = datetime.utcnow

    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    @app.template_test("published")
    def is_published(post) -> bool:
        return getattr(post, "is_published", False)


def _compile_scss(app: Flask) -> None:
    """
    Compile main.scss to main.css using libsass.

    In production or if the CSS is already up to date, skip recompilation
    unless the SCSS source is newer than the output CSS.
    """

    scss_input = app.config.get("SCSS_INPUT", "")
    scss_output = app.config.get("SCSS_OUTPUT", "")
    load_paths = app.config.get("SCSS_LOAD_PATHS", [])

    if not scss_input or not os.path.isfile(scss_input):
        logger.debug("SCSS source not found at %s; skipping compilation.", scss_input)
        return

    if os.path.isfile(scss_output):
        scss_mtime = os.path.getmtime(scss_input)
        css_mtime = os.path.getmtime(scss_output)
        if css_mtime >= scss_mtime and not app.config.get("DEBUG"):
            logger.debug("CSS is up to date; skipping SCSS compilation.")
            return

    try:
        output_style = "compressed" if not app.config.get("DEBUG") else "expanded"
        css = sass.compile(
            filename=scss_input,
            output_style=output_style,
            include_paths=load_paths,
        )
        os.makedirs(os.path.dirname(scss_output), exist_ok=True)
        with open(scss_output, "w", encoding="utf-8") as file_handle:
            file_handle.write(css)
        logger.info("SCSS compiled to %s", scss_output)
    except Exception as exc:  # noqa: BLE001
        logger.warning("SCSS compilation failed: %s", exc)
