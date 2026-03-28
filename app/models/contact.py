from datetime import datetime

from app.extensions import db


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    def mark_read(self) -> None:
        self.is_read = True

    @property
    def short_date(self) -> str:
        return self.created_at.strftime("%b %d, %Y %H:%M")

    @property
    def preview(self) -> str:
        """Return first 120 chars of the message for list views."""
        return self.message[:120] + ("…" if len(self.message) > 120 else "")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.short_date,
        }

    def __repr__(self) -> str:
        return f"<ContactMessage id={self.id} from={self.email!r}>"


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    rating = db.Column(
        db.Integer,
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating"),
        nullable=False,
    )
    message = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    @property
    def stars(self) -> str:
        """Return a unicode star string, e.g. '★★★★☆' for rating 4."""
        filled = "★" * self.rating
        empty = "☆" * (5 - self.rating)
        return filled + empty

    @property
    def short_date(self) -> str:
        return self.created_at.strftime("%b %d, %Y %H:%M")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "rating": self.rating,
            "stars": self.stars,
            "message": self.message,
            "created_at": self.short_date,
        }

    def __repr__(self) -> str:
        return f"<Feedback id={self.id} rating={self.rating} from={self.email!r}>"


class AffiliateLink(db.Model):
    __tablename__ = "affiliate_links"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    cta_text = db.Column(db.String(100), default="Get Deal", nullable=False)
    badge_text = db.Column(
        db.String(60), nullable=True
    )  # e.g. "50% OFF", "Editor's Pick"
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_sidebar = db.Column(
        db.Boolean, default=False, nullable=False
    )  # show in sidebar widget
    clicks = db.Column(db.Integer, default=0, nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)  # display ordering
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def record_click(self) -> None:
        """Atomically increment the click counter."""
        self.clicks = (self.clicks or 0) + 1

    @property
    def short_date(self) -> str:
        return self.created_at.strftime("%b %d, %Y")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "image_url": self.image_url,
            "description": self.description,
            "cta_text": self.cta_text,
            "badge_text": self.badge_text,
            "is_active": self.is_active,
            "is_sidebar": self.is_sidebar,
            "clicks": self.clicks,
            "created_at": self.short_date,
        }

    def __repr__(self) -> str:
        return f"<AffiliateLink id={self.id} title={self.title!r}>"
