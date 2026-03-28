from datetime import datetime

from app.extensions import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)

    # Relationships
    post_id = db.Column(
        db.Integer,
        db.ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Author info
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(255), nullable=True)

    # Content
    content = db.Column(db.Text, nullable=False)

    # Moderation
    is_approved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_spam = db.Column(db.Boolean, default=False, nullable=False)

    # Meta
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ── Relationships ────────────────────────────────────────────────────────
    post = db.relationship("Post", back_populates="comments")

    # Self-referential: parent comment
    parent = db.relationship(
        "Comment",
        remote_side=[id],
        back_populates="replies",
        lazy="select",
    )

    # Child replies
    replies = db.relationship(
        "Comment",
        back_populates="parent",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="asc(Comment.created_at)",
    )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def approve(self) -> None:
        """Approve this comment so it appears publicly."""
        self.is_approved = True

    def mark_spam(self) -> None:
        """Mark this comment as spam (keeps record but hides it)."""
        self.is_spam = True
        self.is_approved = False

    @property
    def approved_replies(self):
        """Return only approved child replies."""
        return (
            self.replies.filter_by(is_approved=True)
            .order_by(Comment.created_at.asc())
            .all()
        )

    @property
    def approved_reply_count(self) -> int:
        return self.replies.filter_by(is_approved=True).count()

    @property
    def is_reply(self) -> bool:
        """Return True if this comment is a reply to another comment."""
        return self.parent_id is not None

    @property
    def short_date(self) -> str:
        return self.created_at.strftime("%b %d, %Y")

    @property
    def iso_date(self) -> str:
        return self.created_at.strftime("%Y-%m-%dT%H:%M:%S")

    @property
    def masked_email(self) -> str:
        """Return a partially masked email for public display."""
        try:
            local, domain = self.email.split("@", 1)
            masked_local = local[:2] + "***" if len(local) > 2 else "***"
            return f"{masked_local}@{domain}"
        except ValueError:
            return "***@***"

    @property
    def avatar_url(self) -> str:
        """Return a Gravatar-style avatar URL based on the commenter's name."""
        initials = "+".join(part[0] for part in self.name.split()[:2]).upper()
        return (
            f"https://ui-avatars.com/api/?name={initials}"
            f"&background=ff7043&color=ffffff&size=64&bold=true"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "post_id": self.post_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "website": self.website,
            "content": self.content,
            "is_approved": self.is_approved,
            "created_at": self.iso_date,
            "reply_count": self.approved_reply_count,
        }

    def __repr__(self) -> str:
        return (
            f"<Comment id={self.id} post_id={self.post_id} approved={self.is_approved}>"
        )
