from datetime import datetime

from app.extensions import db


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)

    # Author + Category
    author_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    # Content
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)

    # Media
    featured_image = db.Column(db.String(255), nullable=True)
    featured_image_alt = db.Column(db.String(200), nullable=True)

    # Status flags
    is_published = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # Counters
    views = db.Column(db.Integer, default=0, nullable=False)

    # SEO
    meta_title = db.Column(db.String(200), nullable=True)
    meta_description = db.Column(db.String(320), nullable=True)
    meta_keywords = db.Column(db.String(255), nullable=True)

    # Monetisation
    affiliate_cta = db.Column(db.Text, nullable=True)  # Raw HTML / markdown block
    affiliate_cta_url = db.Column(db.String(500), nullable=True)
    affiliate_cta_label = db.Column(db.String(120), nullable=True)

    # Embedded media (YouTube / widgets)
    embed_code = db.Column(db.Text, nullable=True)
    embed_caption = db.Column(db.String(255), nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    published_at = db.Column(db.DateTime, nullable=True, index=True)

    # ── Relationships ────────────────────────────────────────────────────────
    author = db.relationship("User", back_populates="posts")
    category = db.relationship("Category", back_populates="posts")
    comments = db.relationship(
        "Comment",
        back_populates="post",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="asc(Comment.created_at)",
    )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def increment_views(self) -> None:
        """Atomically increment the view counter."""
        self.views = (self.views or 0) + 1
        db.session.add(self)
        db.session.commit()

    def publish(self) -> None:
        """Mark the post as published and record the timestamp."""
        self.is_published = True
        if self.published_at is None:
            self.published_at = datetime.utcnow()

    def unpublish(self) -> None:
        self.is_published = False

    @property
    def approved_comments(self):
        """Return only approved top-level comments (no parent)."""
        from app.models.comment import Comment

        return (
            self.comments.filter_by(is_approved=True, parent_id=None)
            .order_by(Comment.created_at.asc())
            .all()
        )

    @property
    def approved_comment_count(self) -> int:
        return self.comments.filter_by(is_approved=True).count()

    @property
    def pending_comment_count(self) -> int:
        return self.comments.filter_by(is_approved=False).count()

    @property
    def effective_meta_title(self) -> str:
        return self.meta_title or self.title

    @property
    def effective_meta_description(self) -> str:
        if self.meta_description:
            return self.meta_description
        if self.excerpt:
            return self.excerpt[:160]
        # Strip HTML tags from content as a last resort
        import re

        clean = re.sub(r"<[^>]+>", "", self.content or "")
        return clean[:160]

    @property
    def featured_image_url(self) -> str | None:
        if self.featured_image:
            return f"/static/uploads/{self.featured_image}"
        return None

    @property
    def reading_time(self) -> int:
        """Estimate reading time in minutes (avg 200 wpm)."""
        import re

        words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", "", self.content or "")))
        return max(1, round(words / 200))

    @property
    def short_date(self) -> str:
        dt = self.published_at or self.created_at
        return dt.strftime("%b %d, %Y")

    @property
    def iso_date(self) -> str:
        dt = self.published_at or self.created_at
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "excerpt": self.excerpt,
            "featured_image_url": self.featured_image_url,
            "author": self.author.username if self.author else None,
            "category": self.category.name if self.category else None,
            "views": self.views,
            "reading_time": self.reading_time,
            "published_at": self.iso_date,
            "is_published": self.is_published,
        }

    def __repr__(self) -> str:
        return f"<Post {self.slug!r}>"
