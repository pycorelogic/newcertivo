from flask import Blueprint, render_template, request, current_app, url_for
from app.extensions import limiter
from app.models.post import Post
from app.models.category import Category
from sqlalchemy import or_
from datetime import datetime
import json
from app.utils.helpers import build_jsonld_article, build_jsonld_breadcrumb, sanitize_html

bp = Blueprint("blog", __name__, url_prefix="/blog")

@bp.route("/")
def list():
    page = request.args.get("page", 1, type=int)
    per_page = 9
    query = Post.query.filter(Post.is_published == True, Post.published_at <= datetime.utcnow()).order_by(Post.published_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        "blog/list.html",
        posts=pagination.items,
        pagination=pagination,
        page_title="Blog"
    )

@bp.route("/category/<slug>")
def category(slug):
    cat = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get("page", 1, type=int)
    per_page = 9
    pagination = Post.query.filter(
        Post.is_published == True, 
        Post.published_at <= datetime.utcnow(),
        Post.category_id == cat.id
    ).order_by(Post.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        "blog/list.html",
        category=cat,
        posts=pagination.items,
        pagination=pagination,
        page_title=f"Category: {cat.name}"
    )

@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 9
    
    query = Post.query.filter(Post.is_published == True, Post.published_at <= datetime.utcnow())
    if q:
        query = query.filter(
            or_(
                Post.title.ilike(f"%{q}%"),
                Post.content.ilike(f"%{q}%"),
                Post.excerpt.ilike(f"%{q}%")
            )
        )
    
    pagination = query.order_by(Post.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
        
    return render_template(
        "blog/list.html",
        q=q,
        posts=pagination.items,
        pagination=pagination,
        page_title=f'Search: "{q}"' if q else "Search"
    )

@bp.route("/<slug>")
def detail(slug):
    post = Post.query.filter(Post.slug == slug, Post.is_published == True, Post.published_at <= datetime.utcnow()).first_or_404()
    post.increment_views()
    
    # Context for breadcrumbs
    site_url = current_app.config.get("SITE_URL", "http://localhost:5000").rstrip("/")
    breadcrumb_items = [
        ("Home", url_for("main.index")),
        ("Blog", url_for("blog.list")),
    ]
    if post.category:
        breadcrumb_items.append((post.category.name, url_for("blog.category", slug=post.category.slug)))
    breadcrumb_items.append((post.title, url_for("blog.detail", slug=post.slug)))
    
    # JSON-LD
    jsonld_article = json.dumps(build_jsonld_article(post, site_url))
    jsonld_breadcrumb = json.dumps(build_jsonld_breadcrumb(breadcrumb_items))
    
    related_posts = []
    if post.category_id:
        related_posts = Post.query.filter(
            Post.is_published == True,
            Post.published_at <= datetime.utcnow(),
            Post.category_id == post.category_id,
            Post.id != post.id
        ).order_by(Post.published_at.desc()).limit(3).all()

    # Previous / Next posts
    prev_post = Post.query.filter(
        Post.is_published == True,
        Post.published_at < post.published_at
    ).order_by(Post.published_at.desc()).first()
    
    next_post = Post.query.filter(
        Post.is_published == True,
        Post.published_at > post.published_at
    ).order_by(Post.published_at.asc()).first()

    # Comments
    from app.models.comment import Comment
    top_comments = Comment.query.filter_by(
        post_id=post.id, 
        parent_id=None, 
        is_approved=True
    ).order_by(Comment.created_at.desc()).all()
        
    return render_template(
        "blog/detail.html",
        post=post,
        related_posts=related_posts,
        prev_post=prev_post,
        next_post=next_post,
        top_comments=top_comments,
        jsonld_article=jsonld_article,
        jsonld_breadcrumb=jsonld_breadcrumb,
        page_title=post.title
    )

@bp.route("/<slug>/comment", methods=["POST"])
@limiter.limit("5 per hour")
def post_comment(slug):
    from flask import flash, redirect, url_for
    from app.extensions import db
    from app.utils.helpers import get_client_ip
    from app.models.comment import Comment

    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    website = request.form.get("website", "").strip()
    content = sanitize_html(request.form.get("content", "").strip())
    parent_id = request.form.get("parent_id")
    
    # Honeypot check
    if request.form.get("phone_number"):
        return redirect(url_for("blog.detail", slug=slug))

    errors = []
    if not name:
        errors.append("Please enter your name.")
    if not email or "@" not in email:
        errors.append("Please enter a valid email address.")
    if not content:
        errors.append("Please enter a comment.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for("blog.detail", slug=slug))

    comment = Comment(
        post_id=post.id,
        name=name,
        email=email,
        website=website or None,
        content=content,
        ip_address=get_client_ip(),
        user_agent=request.user_agent.string if request.user_agent else None
    )
    
    if parent_id:
        try:
            comment.parent_id = int(parent_id)
        except (ValueError, TypeError):
            pass

    db.session.add(comment)
    db.session.commit()
    
    flash("Thank you! Your comment has been submitted and is awaiting moderation.", "success")
    return redirect(url_for("blog.detail", slug=slug))
