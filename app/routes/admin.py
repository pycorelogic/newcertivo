import os
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.models.category import Category
from app.models.comment import Comment
from app.models.contact import AffiliateLink, ContactMessage, Feedback
from app.models.post import Post
from app.models.user import User
from app.utils.decorators import admin_required
from app.utils.helpers import (
    auto_excerpt,
    delete_uploaded_file,
    get_client_ip,
    save_uploaded_file,
    unique_slug,
)

bp = Blueprint("admin", __name__, url_prefix="/admin")


# ─── Dashboard ────────────────────────────────────────────────────────────────


@bp.route("/")
@bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_posts": Post.query.count(),
        "published_posts": Post.query.filter_by(is_published=True).count(),
        "draft_posts": Post.query.filter_by(is_published=False).count(),
        "total_views": db.session.query(db.func.sum(Post.views)).scalar() or 0,
        "total_comments": Comment.query.count(),
        "pending_comments": Comment.query.filter_by(
            is_approved=False, is_spam=False
        ).count(),
        "approved_comments": Comment.query.filter_by(is_approved=True).count(),
        "total_messages": ContactMessage.query.count(),
        "unread_messages": ContactMessage.query.filter_by(is_read=False).count(),
        "total_feedback": Feedback.query.count(),
        "total_categories": Category.query.count(),
        "total_affiliates": AffiliateLink.query.count(),
        "active_affiliates": AffiliateLink.query.filter_by(is_active=True).count(),
    }

    # Recent items for quick overview
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = (
        Comment.query.filter_by(is_approved=False, is_spam=False)
        .order_by(Comment.created_at.desc())
        .limit(5)
        .all()
    )
    recent_messages = (
        ContactMessage.query.filter_by(is_read=False)
        .order_by(ContactMessage.created_at.desc())
        .limit(5)
        .all()
    )

    # Top posts by views
    top_posts = (
        Post.query.filter_by(is_published=True)
        .order_by(Post.views.desc())
        .limit(5)
        .all()
    )

    # Top affiliate links by clicks
    top_affiliates = (
        AffiliateLink.query.order_by(AffiliateLink.clicks.desc()).limit(5).all()
    )

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_posts=recent_posts,
        recent_comments=recent_comments,
        recent_messages=recent_messages,
        top_posts=top_posts,
        top_affiliates=top_affiliates,
    )


# ─── Posts ────────────────────────────────────────────────────────────────────


@bp.route("/posts")
@login_required
@admin_required
def posts():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ADMIN_ITEMS_PER_PAGE", 20)
    status_filter = request.args.get("status", "all")
    category_filter = request.args.get("category", "all")
    search_q = request.args.get("q", "").strip()

    query = Post.query

    if status_filter == "published":
        query = query.filter_by(is_published=True)
    elif status_filter == "draft":
        query = query.filter_by(is_published=False)
    elif status_filter == "featured":
        query = query.filter_by(is_featured=True)

    if category_filter != "all":
        try:
            cat_id = int(category_filter)
            query = query.filter_by(category_id=cat_id)
        except (ValueError, TypeError):
            pass

    if search_q:
        like_q = f"%{search_q}%"
        query = query.filter(
            db.or_(
                Post.title.ilike(like_q),
                Post.excerpt.ilike(like_q),
            )
        )

    pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "admin/posts.html",
        posts=pagination.items,
        pagination=pagination,
        categories=categories,
        status_filter=status_filter,
        category_filter=category_filter,
        search_q=search_q,
    )


@bp.route("/posts/new", methods=["GET", "POST"])
@login_required
@admin_required
def post_create():
    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        excerpt = request.form.get("excerpt", "").strip()
        category_id_raw = request.form.get("category_id", "")
        is_published = request.form.get("is_published") == "on"
        is_featured = request.form.get("is_featured") == "on"
        meta_title = request.form.get("meta_title", "").strip()
        meta_description = request.form.get("meta_description", "").strip()
        meta_keywords = request.form.get("meta_keywords", "").strip()
        affiliate_cta = request.form.get("affiliate_cta", "").strip()
        affiliate_cta_url = request.form.get("affiliate_cta_url", "").strip()
        affiliate_cta_label = request.form.get("affiliate_cta_label", "").strip()
        embed_code = request.form.get("embed_code", "").strip()
        embed_caption = request.form.get("embed_caption", "").strip()
        featured_image_alt = request.form.get("featured_image_alt", "").strip()
        published_at_raw = request.form.get("published_at", "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")

        category_id = None
        if category_id_raw:
            try:
                category_id = int(category_id_raw)
                if not Category.query.get(category_id):
                    errors.append("Selected category does not exist.")
                    category_id = None
            except (ValueError, TypeError):
                errors.append("Invalid category selection.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "admin/post_form.html",
                mode="create",
                categories=categories,
                form_data=request.form,
            )

        # Handle image upload
        featured_image = None
        if "featured_image" in request.files:
            img_file = request.files["featured_image"]
            if img_file and img_file.filename:
                featured_image = save_uploaded_file(img_file, subfolder="posts")
                if featured_image is None:
                    flash(
                        "Image upload failed – unsupported format or file too large.",
                        "warning",
                    )

        # Auto-generate excerpt if not provided
        if not excerpt and content:
            excerpt = auto_excerpt(content, word_count=40)

        slug = unique_slug(title, Post)
        
        parsed_published_at = None
        if published_at_raw:
            try:
                parsed_published_at = datetime.strptime(published_at_raw, "%Y-%m-%dT%H:%M")
            except ValueError:
                pass

        post = Post(
            title=title,
            slug=slug,
            author_id=current_user.id,
            category_id=category_id,
            content=content,
            excerpt=excerpt,
            featured_image=featured_image,
            featured_image_alt=featured_image_alt or title,
            is_published=is_published,
            is_featured=is_featured,
            meta_title=meta_title or title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            affiliate_cta=affiliate_cta,
            affiliate_cta_url=affiliate_cta_url,
            affiliate_cta_label=affiliate_cta_label or "Learn More",
            embed_code=embed_code,
            embed_caption=embed_caption,
            published_at=parsed_published_at,
        )
        if is_published and not parsed_published_at:
            post.publish()

        db.session.add(post)
        db.session.commit()

        flash(f'Post "{post.title}" created successfully!', "success")
        return redirect(url_for("admin.post_edit", post_id=post.id))

    return render_template(
        "admin/post_form.html",
        mode="create",
        categories=categories,
        form_data={},
    )


@bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def post_edit(post_id: int):
    post = Post.query.get_or_404(post_id)
    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        excerpt = request.form.get("excerpt", "").strip()
        category_id_raw = request.form.get("category_id", "")
        is_published = request.form.get("is_published") == "on"
        is_featured = request.form.get("is_featured") == "on"
        meta_title = request.form.get("meta_title", "").strip()
        meta_description = request.form.get("meta_description", "").strip()
        meta_keywords = request.form.get("meta_keywords", "").strip()
        affiliate_cta = request.form.get("affiliate_cta", "").strip()
        affiliate_cta_url = request.form.get("affiliate_cta_url", "").strip()
        affiliate_cta_label = request.form.get("affiliate_cta_label", "").strip()
        embed_code = request.form.get("embed_code", "").strip()
        embed_caption = request.form.get("embed_caption", "").strip()
        featured_image_alt = request.form.get("featured_image_alt", "").strip()
        remove_image = request.form.get("remove_image") == "on"
        regenerate_slug = request.form.get("regenerate_slug") == "on"
        published_at_raw = request.form.get("published_at", "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")

        category_id = None
        if category_id_raw:
            try:
                category_id = int(category_id_raw)
                if not Category.query.get(category_id):
                    errors.append("Selected category does not exist.")
                    category_id = None
            except (ValueError, TypeError):
                errors.append("Invalid category selection.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "admin/post_form.html",
                mode="edit",
                post=post,
                categories=categories,
                form_data=request.form,
            )

        # Handle image upload / removal
        if remove_image and post.featured_image:
            delete_uploaded_file(post.featured_image)
            post.featured_image = None

        if "featured_image" in request.files:
            img_file = request.files["featured_image"]
            if img_file and img_file.filename:
                # Delete old image first
                if post.featured_image:
                    delete_uploaded_file(post.featured_image)
                new_img = save_uploaded_file(img_file, subfolder="posts")
                if new_img:
                    post.featured_image = new_img
                else:
                    flash("Image upload failed – unsupported format.", "warning")

        # Auto-excerpt
        if not excerpt and content:
            excerpt = auto_excerpt(content, word_count=40)

        # Slug regeneration
        if regenerate_slug:
            post.slug = unique_slug(title, Post, existing_id=post.id)

        # Track publish timestamp
        was_published = post.is_published
        
        parsed_published_at = None
        if published_at_raw:
            try:
                parsed_published_at = datetime.strptime(published_at_raw, "%Y-%m-%dT%H:%M")
            except ValueError:
                pass

        post.title = title
        post.content = content
        post.excerpt = excerpt
        post.category_id = category_id
        post.is_published = is_published
        post.is_featured = is_featured
        post.featured_image_alt = featured_image_alt or title
        post.meta_title = meta_title or title
        post.meta_description = meta_description
        post.meta_keywords = meta_keywords
        post.affiliate_cta = affiliate_cta
        post.affiliate_cta_url = affiliate_cta_url
        post.affiliate_cta_label = affiliate_cta_label or "Learn More"
        post.embed_code = embed_code
        post.embed_caption = embed_caption
        post.updated_at = datetime.utcnow()
        if parsed_published_at:
            post.published_at = parsed_published_at

        if is_published and not was_published and not parsed_published_at:
            post.publish()

        db.session.commit()
        flash(f'Post "{post.title}" updated successfully!', "success")
        return redirect(url_for("admin.post_edit", post_id=post.id))

    return render_template(
        "admin/post_form.html",
        mode="edit",
        post=post,
        categories=categories,
        form_data={},
    )


@bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
@admin_required
def post_delete(post_id: int):
    post = Post.query.get_or_404(post_id)
    title = post.title

    # Delete featured image from disk
    if post.featured_image:
        delete_uploaded_file(post.featured_image)

    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{title}" has been deleted.', "info")
    return redirect(url_for("admin.posts"))


@bp.route("/posts/<int:post_id>/toggle-publish", methods=["POST"])
@login_required
@admin_required
def post_toggle_publish(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.is_published:
        post.unpublish()
        msg = f'"{post.title}" has been unpublished.'
    else:
        post.publish()
        msg = f'"{post.title}" has been published.'
    db.session.commit()
    flash(msg, "success")

    referer = request.referrer
    if referer:
        return redirect(referer)
    return redirect(url_for("admin.posts"))


# ─── Categories ───────────────────────────────────────────────────────────────


@bp.route("/categories")
@login_required
@admin_required
def categories():
    cats = Category.query.order_by(Category.name.asc()).all()
    return render_template("admin/categories.html", categories=cats)


@bp.route("/categories/create", methods=["POST"])
@login_required
@admin_required
def category_create():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    color = request.form.get("color", "#2563eb").strip()
    icon = request.form.get("icon", "").strip()

    if not name:
        flash("Category name is required.", "danger")
        return redirect(url_for("admin.categories"))

    if Category.query.filter_by(name=name).first():
        flash(f'A category named "{name}" already exists.', "warning")
        return redirect(url_for("admin.categories"))

    from app.utils.helpers import unique_slug

    slug = unique_slug(name, Category)
    cat = Category(
        name=name, slug=slug, description=description, color=color, icon=icon
    )
    db.session.add(cat)
    db.session.commit()
    flash(f'Category "{name}" created successfully!', "success")
    return redirect(url_for("admin.categories"))


@bp.route("/categories/<int:cat_id>/edit", methods=["POST"])
@login_required
@admin_required
def category_edit(cat_id: int):
    cat = Category.query.get_or_404(cat_id)
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    color = request.form.get("color", "#2563eb").strip()
    icon = request.form.get("icon", "").strip()

    if not name:
        flash("Category name is required.", "danger")
        return redirect(url_for("admin.categories"))

    existing = Category.query.filter(
        Category.name == name, Category.id != cat_id
    ).first()
    if existing:
        flash(f'Another category named "{name}" already exists.', "warning")
        return redirect(url_for("admin.categories"))

    cat.name = name
    cat.description = description
    cat.color = color
    cat.icon = icon
    db.session.commit()
    flash(f'Category "{name}" updated.', "success")
    return redirect(url_for("admin.categories"))


@bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
@admin_required
def category_delete(cat_id: int):
    cat = Category.query.get_or_404(cat_id)
    name = cat.name

    # Nullify category_id on associated posts rather than deleting them
    Post.query.filter_by(category_id=cat_id).update({"category_id": None})
    db.session.delete(cat)
    db.session.commit()
    flash(
        f'Category "{name}" deleted. Associated posts have been uncategorised.', "info"
    )
    return redirect(url_for("admin.categories"))


# ─── Comments ─────────────────────────────────────────────────────────────────


@bp.route("/comments")
@login_required
@admin_required
def comments():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ADMIN_ITEMS_PER_PAGE", 20)
    status_filter = request.args.get("status", "pending")

    query = Comment.query

    if status_filter == "pending":
        query = query.filter_by(is_approved=False, is_spam=False)
    elif status_filter == "approved":
        query = query.filter_by(is_approved=True)
    elif status_filter == "spam":
        query = query.filter_by(is_spam=True)

    pagination = query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    pending_count = Comment.query.filter_by(is_approved=False, is_spam=False).count()

    return render_template(
        "admin/comments.html",
        comments=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        pending_count=pending_count,
    )


@bp.route("/comments/<int:comment_id>/approve", methods=["POST"])
@login_required
@admin_required
def comment_approve(comment_id: int):
    comment = Comment.query.get_or_404(comment_id)
    comment.approve()
    db.session.commit()
    flash("Comment approved and is now publicly visible.", "success")
    referer = request.referrer
    return redirect(referer or url_for("admin.comments"))


@bp.route("/comments/<int:comment_id>/spam", methods=["POST"])
@login_required
@admin_required
def comment_spam(comment_id: int):
    comment = Comment.query.get_or_404(comment_id)
    comment.mark_spam()
    db.session.commit()
    flash("Comment marked as spam.", "warning")
    referer = request.referrer
    return redirect(referer or url_for("admin.comments"))


@bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
@admin_required
def comment_delete(comment_id: int):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment permanently deleted.", "info")
    referer = request.referrer
    return redirect(referer or url_for("admin.comments"))


@bp.route("/comments/bulk-action", methods=["POST"])
@login_required
@admin_required
def comments_bulk_action():
    action = request.form.get("action")
    ids_raw = request.form.getlist("comment_ids")

    if not ids_raw:
        flash("No comments selected.", "warning")
        return redirect(url_for("admin.comments"))

    try:
        ids = [int(i) for i in ids_raw]
    except (ValueError, TypeError):
        flash("Invalid selection.", "danger")
        return redirect(url_for("admin.comments"))

    comments_qs = Comment.query.filter(Comment.id.in_(ids)).all()
    count = len(comments_qs)

    if action == "approve":
        for c in comments_qs:
            c.approve()
        db.session.commit()
        flash(f"{count} comment(s) approved.", "success")
    elif action == "spam":
        for c in comments_qs:
            c.mark_spam()
        db.session.commit()
        flash(f"{count} comment(s) marked as spam.", "warning")
    elif action == "delete":
        for c in comments_qs:
            db.session.delete(c)
        db.session.commit()
        flash(f"{count} comment(s) deleted.", "info")
    else:
        flash("Unknown action.", "danger")

    return redirect(url_for("admin.comments"))


# ─── Contact Messages ─────────────────────────────────────────────────────────


@bp.route("/messages")
@login_required
@admin_required
def messages():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ADMIN_ITEMS_PER_PAGE", 20)
    status_filter = request.args.get("status", "all")

    query = ContactMessage.query
    if status_filter == "unread":
        query = query.filter_by(is_read=False)
    elif status_filter == "read":
        query = query.filter_by(is_read=True)

    pagination = query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    unread_count = ContactMessage.query.filter_by(is_read=False).count()

    return render_template(
        "admin/messages.html",
        messages=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        unread_count=unread_count,
    )


@bp.route("/messages/<int:msg_id>")
@login_required
@admin_required
def message_detail(msg_id: int):
    msg = ContactMessage.query.get_or_404(msg_id)
    if not msg.is_read:
        msg.mark_read()
        db.session.commit()
    return render_template("admin/message_detail.html", message=msg)


@bp.route("/messages/<int:msg_id>/delete", methods=["POST"])
@login_required
@admin_required
def message_delete(msg_id: int):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted.", "info")
    return redirect(url_for("admin.messages"))


# ─── Feedback ─────────────────────────────────────────────────────────────────


@bp.route("/feedback")
@login_required
@admin_required
def feedback():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ADMIN_ITEMS_PER_PAGE", 20)

    pagination = Feedback.query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Rating averages
    all_feedback = Feedback.query.all()
    avg_rating = (
        round(sum(f.rating for f in all_feedback) / len(all_feedback), 1)
        if all_feedback
        else 0
    )
    rating_dist = {i: 0 for i in range(1, 6)}
    for f in all_feedback:
        rating_dist[f.rating] = rating_dist.get(f.rating, 0) + 1

    return render_template(
        "admin/feedback.html",
        feedback_items=pagination.items,
        pagination=pagination,
        avg_rating=avg_rating,
        rating_dist=rating_dist,
        total_feedback=len(all_feedback),
    )


@bp.route("/feedback/<int:fb_id>/delete", methods=["POST"])
@login_required
@admin_required
def feedback_delete(fb_id: int):
    fb = Feedback.query.get_or_404(fb_id)
    db.session.delete(fb)
    db.session.commit()
    flash("Feedback entry deleted.", "info")
    return redirect(url_for("admin.feedback"))


# ─── Affiliate Links ──────────────────────────────────────────────────────────


@bp.route("/affiliates")
@login_required
@admin_required
def affiliates():
    links = AffiliateLink.query.order_by(AffiliateLink.position.asc()).all()
    return render_template("admin/affiliates.html", links=links)


@bp.route("/affiliates/create", methods=["POST"])
@login_required
@admin_required
def affiliate_create():
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()
    image_url = request.form.get("image_url", "").strip()
    description = request.form.get("description", "").strip()
    cta_text = request.form.get("cta_text", "Get Deal").strip()
    badge_text = request.form.get("badge_text", "").strip()
    is_active = request.form.get("is_active") == "on"
    is_sidebar = request.form.get("is_sidebar") == "on"
    position_raw = request.form.get("position", "0")

    errors = []
    if not title:
        errors.append("Title is required.")
    if not url or not url.startswith(("http://", "https://")):
        errors.append("A valid URL (starting with http:// or https://) is required.")

    try:
        position = int(position_raw)
    except (ValueError, TypeError):
        position = 0

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for("admin.affiliates"))

    link = AffiliateLink(
        title=title,
        url=url,
        image_url=image_url or None,
        description=description,
        cta_text=cta_text or "Get Deal",
        badge_text=badge_text or None,
        is_active=is_active,
        is_sidebar=is_sidebar,
        position=position,
    )
    db.session.add(link)
    db.session.commit()
    flash(f'Affiliate link "{title}" created.', "success")
    return redirect(url_for("admin.affiliates"))


@bp.route("/affiliates/<int:link_id>/edit", methods=["POST"])
@login_required
@admin_required
def affiliate_edit(link_id: int):
    link = AffiliateLink.query.get_or_404(link_id)
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()
    image_url = request.form.get("image_url", "").strip()
    description = request.form.get("description", "").strip()
    cta_text = request.form.get("cta_text", "Get Deal").strip()
    badge_text = request.form.get("badge_text", "").strip()
    is_active = request.form.get("is_active") == "on"
    is_sidebar = request.form.get("is_sidebar") == "on"
    position_raw = request.form.get("position", "0")

    errors = []
    if not title:
        errors.append("Title is required.")
    if not url or not url.startswith(("http://", "https://")):
        errors.append("A valid URL is required.")

    try:
        position = int(position_raw)
    except (ValueError, TypeError):
        position = link.position

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for("admin.affiliates"))

    link.title = title
    link.url = url
    link.image_url = image_url or None
    link.description = description
    link.cta_text = cta_text or "Get Deal"
    link.badge_text = badge_text or None
    link.is_active = is_active
    link.is_sidebar = is_sidebar
    link.position = position
    db.session.commit()
    flash(f'Affiliate link "{title}" updated.', "success")
    return redirect(url_for("admin.affiliates"))


@bp.route("/affiliates/<int:link_id>/delete", methods=["POST"])
@login_required
@admin_required
def affiliate_delete(link_id: int):
    link = AffiliateLink.query.get_or_404(link_id)
    title = link.title
    db.session.delete(link)
    db.session.commit()
    flash(f'Affiliate link "{title}" deleted.', "info")
    return redirect(url_for("admin.affiliates"))


@bp.route("/affiliates/<int:link_id>/toggle", methods=["POST"])
@login_required
@admin_required
def affiliate_toggle(link_id: int):
    link = AffiliateLink.query.get_or_404(link_id)
    link.is_active = not link.is_active
    db.session.commit()
    state = "activated" if link.is_active else "deactivated"
    flash(f'"{link.title}" has been {state}.', "success")
    return redirect(url_for("admin.affiliates"))


# ─── Media / Upload Manager ───────────────────────────────────────────────────


@bp.route("/media")
@login_required
@admin_required
def media():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    images = []

    if os.path.isdir(upload_folder):
        for root, dirs, files in os.walk(upload_folder):
            for filename in files:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, upload_folder).replace("\\", "/")
                ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                if ext in {"png", "jpg", "jpeg", "gif", "webp", "svg"}:
                    images.append(
                        {
                            "filename": filename,
                            "rel_path": rel_path,
                            "url": f"/static/uploads/{rel_path}",
                            "size": os.path.getsize(filepath),
                        }
                    )

    images.sort(key=lambda x: x["filename"])
    return render_template("admin/media.html", images=images)


@bp.route("/media/upload", methods=["POST"])
@login_required
@admin_required
def media_upload():
    if "file" not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for("admin.media"))

    file = request.files["file"]
    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(url_for("admin.media"))

    saved = save_uploaded_file(file)
    if saved:
        flash(f"File uploaded successfully: {saved}", "success")
    else:
        flash("Upload failed – unsupported format or file too large.", "danger")
    return redirect(url_for("admin.media"))


@bp.route("/media/delete", methods=["POST"])
@login_required
@admin_required
def media_delete():
    filename = request.form.get("filename", "").strip()
    if not filename:
        flash("No filename specified.", "danger")
        return redirect(url_for("admin.media"))

    # Security: prevent path traversal
    safe_filename = os.path.basename(filename)
    if delete_uploaded_file(safe_filename):
        flash(f"File '{safe_filename}' deleted.", "info")
    else:
        flash("File not found or could not be deleted.", "danger")
    return redirect(url_for("admin.media"))


# ─── JSON API (used by the rich-text editor image picker) ─────────────────────


@bp.route("/api/images")
@login_required
@admin_required
def api_images():
    """Return a JSON list of all uploaded images for the editor image picker."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    images = []

    if os.path.isdir(upload_folder):
        for root, dirs, files in os.walk(upload_folder):
            for filename in files:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, upload_folder).replace("\\", "/")
                ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                if ext in {"png", "jpg", "jpeg", "gif", "webp", "svg"}:
                    images.append(
                        {
                            "url": f"/static/uploads/{rel_path}",
                            "filename": filename,
                            "size": os.path.getsize(filepath),
                        }
                    )

    return jsonify(images)


@bp.route("/api/upload-image", methods=["POST"])
@login_required
@admin_required
def api_upload_image():
    """Handle inline image uploads from the rich-text editor (returns JSON)."""
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    saved = save_uploaded_file(file, subfolder="editor")
    if saved:
        return jsonify({"url": f"/static/uploads/{saved}"})
    return jsonify(
        {"error": "Upload failed – unsupported format or file too large."}
    ), 400


@bp.route("/api/stats")
@login_required
@admin_required
def api_stats():
    """Return live dashboard stats as JSON (for AJAX refresh)."""
    return jsonify(
        {
            "pending_comments": Comment.query.filter_by(
                is_approved=False, is_spam=False
            ).count(),
            "unread_messages": ContactMessage.query.filter_by(is_read=False).count(),
            "total_posts": Post.query.filter_by(is_published=True).count(),
            "draft_posts": Post.query.filter_by(is_published=False).count(),
        }
    )
