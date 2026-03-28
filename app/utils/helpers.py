import os
import re
import uuid
from datetime import datetime
from typing import Optional

from flask import current_app
from slugify import slugify as python_slugify
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# ─── Slug Utilities ──────────────────────────────────────────────────────────


def generate_slug(text: str) -> str:
    """Generate a URL-safe slug from any string."""
    return python_slugify(text, max_length=200, word_boundary=True, separator="-")


def unique_slug(
    text: str, model, field="slug", existing_id: Optional[int] = None
) -> str:
    """
    Generate a unique slug for a given model class.
    If a slug already exists, appends a numeric suffix until unique.

    :param text:        Source text to slugify.
    :param model:       SQLAlchemy model class to check uniqueness against.
    :param field:       Column name to check (default: "slug").
    :param existing_id: ID of the record being updated so we don't conflict with itself.
    """
    base_slug = generate_slug(text)
    slug = base_slug
    counter = 1

    while True:
        query = model.query.filter(getattr(model, field) == slug)
        if existing_id is not None:
            query = query.filter(model.id != existing_id)
        if query.first() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


# ─── File Upload Utilities ───────────────────────────────────────────────────


def allowed_file(filename: str) -> bool:
    """Return True if the file has an allowed extension."""
    allowed = current_app.config.get(
        "ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"}
    )
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def save_uploaded_file(file: FileStorage, subfolder: str = "") -> Optional[str]:
    """
    Validate and persist an uploaded FileStorage object.

    Returns the saved filename (relative to UPLOAD_FOLDER) on success,
    or None if the file is empty / has a disallowed extension.
    """
    try:
        if not current_app.config.get("UPLOADS_ENABLED", True):
            current_app.logger.warning("Upload skipped because uploads are disabled.")
            return None

        if not file or not file.filename:
            return None

        filename = secure_filename(file.filename)
        if not filename or not allowed_file(filename):
            return None

        ext = filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"

        upload_dir = current_app.config["UPLOAD_FOLDER"]
        if subfolder:
            upload_dir = os.path.join(upload_dir, subfolder)

        os.makedirs(upload_dir, exist_ok=True)

        save_path = os.path.join(upload_dir, unique_name)
        file.save(save_path)
        
        current_app.logger.info(f"File uploaded successfully: {save_path}")

        return (
            os.path.join(subfolder, unique_name).replace("\\", "/")
            if subfolder
            else unique_name
        )
    except Exception as e:
        current_app.logger.error(f"File upload error: {e}", exc_info=True)
        return None


def delete_uploaded_file(filename: Optional[str]) -> bool:
    """
    Delete a previously uploaded file from the uploads folder.
    Returns True if deleted, False otherwise.
    """
    if not filename:
        return False

    if not current_app.config.get("UPLOADS_ENABLED", True):
        return False

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_dir, filename)

    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
            return True
        except OSError:
            return False
    return False


# ─── Content / Text Utilities ────────────────────────────────────────────────

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(html: str) -> str:
    """Strip all HTML tags from a string."""
    text = _HTML_TAG_RE.sub(" ", html or "")
    return _WHITESPACE_RE.sub(" ", text).strip()


def truncate(text: str, length: int = 160, suffix: str = "…") -> str:
    """Truncate plain text to *length* characters without cutting a word."""
    text = strip_html(text)
    if len(text) <= length:
        return text
    # Walk back to the last space boundary
    truncated = text[:length]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + suffix


def auto_excerpt(content: str, word_count: int = 40) -> str:
    """
    Generate an excerpt from HTML content by taking the first *word_count* words.
    """
    plain = strip_html(content)
    words = plain.split()
    if len(words) <= word_count:
        return plain
    return " ".join(words[:word_count]) + "…"


def reading_time(content: str) -> int:
    """Estimate reading time in minutes (average 200 words per minute)."""
    plain = strip_html(content)
    words = len(re.findall(r"\w+", plain))
    return max(1, round(words / 200))


# ─── Pagination Helper ───────────────────────────────────────────────────────


def paginate_query(query, page: int, per_page: int):
    """
    Thin wrapper around SQLAlchemy's paginate() that returns a
    Flask-SQLAlchemy Pagination object (or equivalent).
    """
    return query.paginate(page=page, per_page=per_page, error_out=False)


# ─── Date / Time Utilities ───────────────────────────────────────────────────


def human_date(dt: Optional[datetime]) -> str:
    """Return a human-readable date string, e.g. 'Jan 05, 2025'."""
    if dt is None:
        return ""
    return dt.strftime("%b %d, %Y")


def human_datetime(dt: Optional[datetime]) -> str:
    """Return a human-readable datetime string, e.g. 'Jan 05, 2025 14:30'."""
    if dt is None:
        return ""
    return dt.strftime("%b %d, %Y %H:%M")


def time_ago(dt: Optional[datetime]) -> str:
    """Return a relative time string, e.g. '3 hours ago'."""
    if dt is None:
        return ""
    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        m = seconds // 60
        return f"{m} minute{'s' if m != 1 else ''} ago"
    elif seconds < 86400:
        h = seconds // 3600
        return f"{h} hour{'s' if h != 1 else ''} ago"
    elif seconds < 604800:
        d = seconds // 86400
        return f"{d} day{'s' if d != 1 else ''} ago"
    elif seconds < 2592000:
        w = seconds // 604800
        return f"{w} week{'s' if w != 1 else ''} ago"
    elif seconds < 31536000:
        mo = seconds // 2592000
        return f"{mo} month{'s' if mo != 1 else ''} ago"
    else:
        y = seconds // 31536000
        return f"{y} year{'s' if y != 1 else ''} ago"


# ─── IP / Request Helpers ────────────────────────────────────────────────────


def get_client_ip() -> str:
    """
    Return the real client IP, respecting X-Forwarded-For headers
    set by reverse proxies (e.g. Nginx, Cloudflare).
    """
    from flask import request

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For may be a comma-separated list; take the first (client) IP
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


# ─── SEO / Structured Data ───────────────────────────────────────────────────


def build_jsonld_article(post, site_url: str) -> dict:
    """Build a JSON-LD Article structured-data dict for a blog post."""
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.effective_meta_description,
        "image": (
            f"{site_url}{post.featured_image_url}" if post.featured_image_url else None
        ),
        "author": {
            "@type": "Person",
            "name": post.author.username if post.author else "Unknown",
        },
        "publisher": {
            "@type": "Organization",
            "name": site_url,
        },
        "datePublished": post.iso_date,
        "dateModified": post.updated_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "url": f"{site_url}/blog/{post.slug}",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"{site_url}/blog/{post.slug}",
        },
        "keywords": post.meta_keywords or "",
        "articleSection": post.category.name if post.category else "",
    }


def build_jsonld_breadcrumb(items: list[tuple[str, str]]) -> dict:
    """
    Build a JSON-LD BreadcrumbList.

    :param items: list of (name, url) tuples in order.
    """
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": url,
            }
            for i, (name, url) in enumerate(items)
        ],
    }


# ─── Sanitisation ────────────────────────────────────────────────────────────


def sanitize_html(raw_html: str) -> str:
    """
    Sanitise user-supplied HTML, allowing only a safe subset of tags.
    Uses the `bleach` library.
    """
    try:
        import bleach

        ALLOWED_TAGS = [
            "p",
            "br",
            "strong",
            "b",
            "em",
            "i",
            "u",
            "s",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "blockquote",
            "pre",
            "code",
            "a",
            "img",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "hr",
            "span",
            "div",
        ]
        ALLOWED_ATTRS = {
            "a": ["href", "title", "target", "rel"],
            "img": ["src", "alt", "width", "height", "loading"],
            "code": ["class"],
            "span": ["class", "style"],
            "div": ["class"],
            "td": ["colspan", "rowspan"],
            "th": ["colspan", "rowspan", "scope"],
        }
        return bleach.clean(
            raw_html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            strip=True,
        )
    except ImportError:
        # bleach not installed — fall back to stripping all tags
        return strip_html(raw_html)
