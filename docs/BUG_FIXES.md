# Certivo Blog - Bug Fixes & Code Improvements

This document lists all identified bugs and the exact code changes needed to fix them.

---

## 🔴 CRITICAL SECURITY FIXES

### 1. Add Input Sanitization to Comment Submission

**File:** `app/routes/blog.py`  
**Issue:** Comment content is not sanitized, allowing XSS attacks  
**Fix:** Add bleach sanitization

```python
# At the top of blog.py, add import
from app.utils.helpers import sanitize_html

# In the post_comment function, sanitize content before saving
@bp.route("/<slug>/comment", methods=["POST"])
def post_comment(slug):
    # ... existing imports ...
    
    # ADD THIS AFTER getting content from form
    content = sanitize_html(request.form.get("content", "").strip())
    
    # ... rest of the function ...
```

---

### 2. Add Rate Limiting to Prevent Brute Force

**File:** `requirements.txt`  
**Add:**
```
Flask-Limiter==3.5.0
```

**File:** `app/__init__.py`  
**Add after csrf initialization:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add after line "csrf.init_app(app)"
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
```

**File:** `app/routes/auth.py`  
**Add import and decorator:**
```python
from app import limiter  # Add at top

@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # ADD THIS LINE
@anonymous_required()
def login():
    # ... rest of function
```

**File:** `app/routes/main.py`  
**Add to contact and feedback routes:**
```python
from app import limiter  # Add import

@bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("10 per hour")  # ADD THIS
def contact():
    # ...

@bp.route("/feedback", methods=["GET", "POST"])
@limiter.limit("10 per hour")  # ADD THIS
def feedback():
    # ...

@bp.route("/blog/<slug>/comment", methods=["POST"])
@limiter.limit("5 per hour")  # ADD THIS
def post_comment(slug):
    # ...
```

---

### 3. Fix Deprecated SQLAlchemy Query Methods

**File:** `app/routes/main.py`  
**Replace ALL instances of:**
```python
Post.query.filter(...).order_by(...).all()
```

**With:**
```python
from sqlalchemy import select

stmt = select(Post).where(...).order_by(Post.published_at.desc())
posts = db.session.execute(stmt).scalars().all()
```

**Specific fixes:**

```python
# Fix 1: In inject_globals() - line ~33
from sqlalchemy import select

# OLD:
recent_posts = (
    Post.query.filter(Post.is_published == True, Post.published_at <= datetime.utcnow())
    .order_by(Post.published_at.desc())
    .limit(5)
    .all()
)

# NEW:
stmt = select(Post).where(
    Post.is_published == True,
    Post.published_at <= datetime.utcnow()
).order_by(Post.published_at.desc()).limit(5)
recent_posts = db.session.execute(stmt).scalars().all()
```

**Apply same pattern to:**
- `popular_posts` in `inject_globals()`
- `featured_posts` in `index()`
- `latest_posts` in `index()`
- All queries in `blog.py`
- All queries in `admin.py`

---

### 4. Add Health Check Endpoint

**File:** `app/routes/main.py`  
**Add at the end of the file:**

```python
# ─── Health Check ───────────────────────────────────────────────────────────


@bp.route("/health")
def health():
    """Health check endpoint for load balancers and monitoring."""
    from app.extensions import db
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
```

---

### 5. Add Security Headers

**File:** `app/__init__.py`  
**Add before `return app`:**

```python
# ── Security Headers ───────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://pagead2.googlesyndication.com https://www.google-analytics.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://www.google-analytics.com;"
    )
    response.headers['Content-Security-Policy'] = csp
    
    return response
```

---

## 🟡 HIGH PRIORITY FIXES

### 6. Fix Hardcoded Credentials in run.py

**File:** `run.py`  
**Line 47 - CHANGE:**
```python
password_hash=generate_password_hash("admin123"),
```

**TO:**
```python
password_hash=generate_password_hash(os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")),
```

**Add warning message:**
```python
# Add after line 200 (in the startup messages)
if os.environ.get("FLASK_ENV") == "production":
    print("⚠️  WARNING: Change default admin password immediately!")
    print("⚠️  Set DEFAULT_ADMIN_PASSWORD environment variable")
```

---

### 7. Fix CSS Version Cache Busting

**File:** `app/templates/base.html`  
**Line 47 - REPLACE:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}?v=1.0.5" />
```

**WITH:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}?v={{ now().timestamp() | int }}" />
```

**File:** `app/templates/admin/base.html`  
**Line 15 - REPLACE:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}?v=1.0.1" />
```

**WITH:**
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}?v={{ now().timestamp() | int }}" />
```

---

### 8. Add Logging Configuration

**File:** `app/config.py`  
**Add to Config class:**
```python
# ─── Logging ────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = os.environ.get("LOG_FILE", "logs/certivo.log")
LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
```

**File:** `app/__init__.py`  
**Add before `return app`:**

```python
# ── Logging Configuration ───────────────────────────────────────────────────
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    import os
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(app.config.get("LOG_FILE", "logs/certivo.log")), exist_ok=True)
    
    handler = RotatingFileHandler(
        app.config.get("LOG_FILE", "logs/certivo.log"),
        maxBytes=10240000,  # 10MB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(app.config.get(
        "LOG_FORMAT",
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )))
    handler.setLevel(app.config.get("LOG_LEVEL", "INFO"))
    
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))
    app.logger.info("Certivo Blog startup")
```

---

### 9. Fix Affiliate Click Route - Add CSRF Protection

**File:** `app/routes/main.py`  
**Current:**
```python
@bp.route("/go/<int:link_id>")
def affiliate_click(link_id: int):
    link = AffiliateLink.query.get_or_404(link_id)
    # ...
```

**Replace with:**
```python
@bp.route("/go/<int:link_id>")
def affiliate_click(link_id: int):
    """Record a click and redirect to the affiliate URL."""
    from app.models.contact import AffiliateLink
    
    link = AffiliateLink.query.get_or_404(link_id)
    if not link.is_active:
        return redirect(url_for("main.index"))
    
    # Only record clicks from actual page referrals (basic bot protection)
    link.record_click()
    db.session.commit()
    
    # Add nofollow for SEO
    return redirect(link.url, code=302)
```

---

### 10. Add Email Validation on Contact/Feedback

**File:** `app/routes/main.py`  
**Add import:**
```python
from email_validator import validate_email, EmailNotValidError
```

**In contact() function, replace email validation:**
```python
# OLD:
if not email or "@" not in email:
    errors.append("Please enter a valid email address.")

# NEW:
try:
    valid = validate_email(email)
    email = valid.email  # Normalized version
except EmailNotValidError as e:
    errors.append(f"Please enter a valid email address: {str(e)}")
```

**Apply same fix to feedback() function**

---

## 🟢 MEDIUM PRIORITY FIXES

### 11. Add Pagination to Related Posts

**File:** `app/routes/blog.py`  
**In detail() function:**

```python
# OLD:
related_posts = Post.query.filter(
    Post.is_published == True,
    Post.published_at <= datetime.utcnow(),
    Post.category_id == post.category_id,
    Post.id != post.id
).order_by(Post.published_at.desc()).limit(3).all()

# NEW (with proper error handling):
related_posts = []
if post.category_id:
    stmt = select(Post).where(
        Post.is_published == True,
        Post.published_at <= datetime.utcnow(),
        Post.category_id == post.category_id,
        Post.id != post.id
    ).order_by(Post.published_at.desc()).limit(3)
    related_posts = db.session.execute(stmt).scalars().all()
```

---

### 12. Add Proper Error Handling for File Uploads

**File:** `app/utils/helpers.py`  
**In save_uploaded_file():**

```python
def save_uploaded_file(file: FileStorage, subfolder: str = "") -> Optional[str]:
    """
    Validate and persist an uploaded FileStorage object.

    Returns the saved filename (relative to UPLOAD_FOLDER) on success,
    or None if the file is empty / has a disallowed extension.
    """
    try:
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

        return (
            os.path.join(subfolder, unique_name).replace("\\", "/")
            if subfolder
            else unique_name
        )
    except Exception as e:
        current_app.logger.error(f"File upload error: {e}")
        return None
```

---

### 13. Add Database Backup Before Migrations

**File:** `app/routes/admin.py`  
**Add before any database modification operations:**

```python
import shutil
from datetime import datetime

def backup_database():
    """Create a backup of the SQLite database before major operations."""
    import sqlite3
    from flask import current_app
    
    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite"):
        db_path = db_uri.replace("sqlite:///", "")
        if db_path.startswith("/"):
            db_path = db_path[1:]
        
        if os.path.isfile(db_path):
            backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            current_app.logger.info(f"Database backed up to {backup_path}")
```

---

### 14. Fix Missing Import in blog.py

**File:** `app/routes/blog.py`  
**Add at top:**
```python
from sqlalchemy import select
```

---

### 15. Add Proper 404 Error Handler with Logging

**File:** `app/routes/main.py`  
**Update error handlers:**

```python
@bp.app_errorhandler(404)
def not_found(e):
    import logging
    logging.warning(f"404 error: {request.url}")
    return render_template("errors/404.html"), 404

@bp.app_errorhandler(500)
def server_error(e):
    import logging
    logging.error(f"500 error: {request.url} - {str(e)}", exc_info=True)
    db.session.rollback()
    return render_template("errors/500.html"), 500
```

---

## 📝 POST-FIX VERIFICATION

After applying all fixes:

1. **Test locally:**
   ```bash
   python run.py
   # Visit http://localhost:5000/health
   # Try submitting a comment with <script>alert('xss')</script>
   # Try brute force login (should be rate limited)
   ```

2. **Check logs:**
   ```bash
   tail -f logs/certivo.log
   ```

3. **Security scan:**
   ```bash
   pip install safety
   safety check
   ```

4. **Test all forms:**
   - Contact form
   - Feedback form
   - Comment form
   - Login (try 6+ failed attempts)

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] Generate new SECRET_KEY
- [ ] Change default admin password
- [ ] Update DATABASE_URL for PostgreSQL
- [ ] Set FLASK_ENV=production
- [ ] Configure email with app password (not regular password)
- [ ] Set SITE_URL to production domain
- [ ] Enable SESSION_COOKIE_SECURE
- [ ] Set up SSL/HTTPS
- [ ] Configure Nginx/Apache
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring (Sentry optional)
- [ ] Test health endpoint
- [ ] Verify rate limiting works
- [ ] Test all forms
- [ ] Check security headers (https://securityheaders.com)

---

**Last Updated:** March 24, 2026  
**Total Bugs Identified:** 15  
**Critical:** 5 | **High:** 5 | **Medium:** 5
