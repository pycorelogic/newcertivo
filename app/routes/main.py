import json
from datetime import datetime

from email_validator import validate_email, EmailNotValidError
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.extensions import db, limiter
from app.models.category import Category
from app.models.contact import AffiliateLink, ContactMessage, Feedback
from app.models.post import Post
from app.utils.email_utils import send_contact_notification
from app.utils.helpers import get_client_ip

bp = Blueprint("main", __name__)


# ─── Context Processors ───────────────────────────────────────────────────────


@bp.app_context_processor
def inject_globals():
    """Inject site-wide variables into every template context."""
    categories = Category.query.order_by(Category.name.asc()).all()
    recent_posts = (
        Post.query.filter(Post.is_published == True, Post.published_at <= datetime.utcnow())
        .order_by(Post.published_at.desc())
        .limit(5)
        .all()
    )
    popular_posts = (
        Post.query.filter(Post.is_published == True, Post.published_at <= datetime.utcnow())
        .order_by(Post.views.desc())
        .limit(5)
        .all()
    )
    sidebar_affiliates = (
        AffiliateLink.query.filter_by(is_active=True, is_sidebar=True)
        .order_by(AffiliateLink.position.asc())
        .limit(3)
        .all()
    )
    return dict(
        site_name=current_app.config.get("SITE_NAME", "Certivo"),
        site_tagline=current_app.config.get(
            "SITE_TAGLINE", "Insights, Ideas & Innovation"
        ),
        site_url=current_app.config.get("SITE_URL", "http://localhost:5000"),
        site_description=current_app.config.get("SITE_DESCRIPTION", ""),
        site_author=current_app.config.get("SITE_AUTHOR", ""),
        site_twitter=current_app.config.get("SITE_TWITTER", ""),
        adsense_client_id=current_app.config.get("ADSENSE_CLIENT_ID", ""),
        adsense_enabled=current_app.config.get("ADSENSE_ENABLED", False),
        ga_tracking_id=current_app.config.get("GA_TRACKING_ID", ""),
        nav_categories=categories,
        sidebar_recent_posts=recent_posts,
        sidebar_popular_posts=popular_posts,
        sidebar_affiliates=sidebar_affiliates,
        current_year=datetime.utcnow().year,
    )


# ─── Home ─────────────────────────────────────────────────────────────────────


@bp.route("/")
def index():
    # Featured posts (hero section)
    featured_posts = (
        Post.query.filter(Post.is_published == True, Post.is_featured == True, Post.published_at <= datetime.utcnow())
        .order_by(Post.published_at.desc())
        .limit(3)
        .all()
    )

    # Latest posts grid
    latest_posts = (
        Post.query.filter(Post.is_published == True, Post.published_at <= datetime.utcnow())
        .order_by(Post.published_at.desc())
        .limit(6)
        .all()
    )

    # Popular posts (sidebar / section)
    popular_posts = (
        Post.query.filter(Post.is_published == True, Post.published_at <= datetime.utcnow())
        .order_by(Post.views.desc())
        .limit(4)
        .all()
    )

    # All categories with post counts
    categories = Category.query.order_by(Category.name.asc()).all()

    # Sidebar affiliates (inline cards on homepage)
    affiliate_cards = (
        AffiliateLink.query.filter_by(is_active=True)
        .order_by(AffiliateLink.position.asc())
        .limit(4)
        .all()
    )

    return render_template(
        "index.html",
        featured_posts=featured_posts,
        latest_posts=latest_posts,
        popular_posts=popular_posts,
        categories=categories,
        affiliate_cards=affiliate_cards,
    )


# ─── About ────────────────────────────────────────────────────────────────────


@bp.route("/about")
def about():
    total_posts = Post.query.filter(Post.is_published == True, Post.published_at <= datetime.utcnow()).count()
    total_categories = Category.query.count()
    return render_template(
        "pages/about.html",
        total_posts=total_posts,
        total_categories=total_categories,
    )


# ─── Contact ──────────────────────────────────────────────────────────────────


@bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        # Basic validation
        errors = []
        if not name:
            errors.append("Please enter your name.")
        
        # Email validation with email-validator
        try:
            valid = validate_email(email)
            email = valid.email  # Normalized version
        except EmailNotValidError as e:
            errors.append(f"Please enter a valid email address: {str(e)}")
        
        if not subject:
            errors.append("Please enter a subject.")
        if not message:
            errors.append("Please enter a message.")
        if len(message) > 5000:
            errors.append("Your message is too long (max 5 000 characters).")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "pages/contact.html",
                form_data={
                    "name": name,
                    "email": email,
                    "subject": subject,
                    "message": message,
                },
            )

        # Persist to database
        msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
            ip_address=get_client_ip(),
        )
        db.session.add(msg)
        db.session.commit()

        # Send email notifications (non-blocking failure)
        try:
            send_contact_notification(
                name=name, email=email, subject=subject, message=message
            )
        except Exception:
            pass  # mail errors must not break the user flow

        flash(
            "Thank you for your message! We'll get back to you within 1–2 business days.",
            "success",
        )
        return redirect(url_for("main.contact"))

    return render_template("pages/contact.html", form_data={})


# ─── Feedback ─────────────────────────────────────────────────────────────────


@bp.route("/feedback", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def feedback():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        rating_raw = request.form.get("rating", "")
        message = request.form.get("message", "").strip()

        errors = []
        if not name:
            errors.append("Please enter your name.")
        
        # Email validation with email-validator
        try:
            valid = validate_email(email)
            email = valid.email  # Normalized version
        except EmailNotValidError as e:
            errors.append(f"Please enter a valid email address: {str(e)}")
        
        try:
            rating = int(rating_raw)
            if not 1 <= rating <= 5:
                raise ValueError
        except (ValueError, TypeError):
            rating = None
            errors.append("Please select a rating between 1 and 5.")
        if not message:
            errors.append("Please enter your feedback message.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "pages/feedback.html",
                form_data={
                    "name": name,
                    "email": email,
                    "rating": rating_raw,
                    "message": message,
                },
            )

        fb = Feedback(
            name=name,
            email=email,
            rating=rating,
            message=message,
            ip_address=get_client_ip(),
        )
        db.session.add(fb)
        db.session.commit()

        flash(
            "Thank you for your feedback! We really appreciate it. 🙏",
            "success",
        )
        return redirect(url_for("main.feedback"))

    return render_template("pages/feedback.html", form_data={})


# ─── Search (redirect to blog search) ────────────────────────────────────────


@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    return redirect(url_for("blog.search", q=q))


# ─── Affiliate click tracker ──────────────────────────────────────────────────


@bp.route("/go/<int:link_id>")
def affiliate_click(link_id: int):
    """Record a click and redirect to the affiliate URL."""
    link = AffiliateLink.query.get_or_404(link_id)
    if not link.is_active:
        return redirect(url_for("main.index"))
    link.record_click()
    db.session.commit()
    return redirect(link.url)


# ─── SEO: Sitemap ─────────────────────────────────────────────────────────────


@bp.route("/sitemap.xml")
def sitemap():
    site_url = current_app.config.get("SITE_URL", "http://localhost:5000").rstrip("/")

    pages = []

    # Static pages
    static_routes = [
        ("main.index", {}, "weekly", "1.0"),
        ("blog.list", {}, "daily", "0.9"),
        ("main.about", {}, "monthly", "0.6"),
        ("main.contact", {}, "monthly", "0.5"),
        ("main.feedback", {}, "monthly", "0.5"),
    ]
    for endpoint, kwargs, changefreq, priority in static_routes:
        try:
            pages.append(
                {
                    "loc": site_url + url_for(endpoint, **kwargs),
                    "changefreq": changefreq,
                    "priority": priority,
                    "lastmod": datetime.utcnow().strftime("%Y-%m-%d"),
                }
            )
        except Exception:
            pass

    # Category pages
    for cat in Category.query.all():
        pages.append(
            {
                "loc": site_url + url_for("blog.category", slug=cat.slug),
                "changefreq": "weekly",
                "priority": "0.7",
                "lastmod": datetime.utcnow().strftime("%Y-%m-%d"),
            }
        )

    # Blog posts
    posts = (
        Post.query.filter_by(is_published=True).order_by(Post.published_at.desc()).all()
    )
    for post in posts:
        pages.append(
            {
                "loc": site_url + url_for("blog.detail", slug=post.slug),
                "changefreq": "monthly",
                "priority": "0.8",
                "lastmod": post.updated_at.strftime("%Y-%m-%d"),
            }
        )

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for page in pages:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{page['loc']}</loc>")
        xml_lines.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{page['priority']}</priority>")
        xml_lines.append(f"    <lastmod>{page['lastmod']}</lastmod>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")

    return Response("\n".join(xml_lines), mimetype="application/xml")


# ─── SEO: robots.txt ─────────────────────────────────────────────────────────


@bp.route("/robots.txt")
def robots():
    site_url = current_app.config.get("SITE_URL", "http://localhost:5000").rstrip("/")
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /auth/
Disallow: /go/

Sitemap: {site_url}/sitemap.xml
"""
    return Response(content, mimetype="text/plain")


# ─── Health Check ───────────────────────────────────────────────────────────


@bp.route("/health")
def health():
    """Health check endpoint for load balancers and monitoring."""
    from sqlalchemy import text

    try:
        # Check database connection
        db.session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }, 200 if db_status == "ok" else 503


# ─── Error Handlers ───────────────────────────────────────────────────────────


@bp.app_errorhandler(404)
def not_found(e):
    import logging
    logging.warning(f"404 error: {request.url}")
    return render_template("errors/404.html"), 404


@bp.app_errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@bp.app_errorhandler(500)
def server_error(e):
    import logging
    logging.error(f"500 error: {request.url} - {str(e)}", exc_info=True)
    db.session.rollback()
    return render_template("errors/500.html"), 500
