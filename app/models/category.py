from datetime import datetime

from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default="#2563eb", nullable=False)
    icon = db.Column(db.String(50), nullable=True)  # e.g. "fas fa-laptop"
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    posts = db.relationship(
        "Post",
        back_populates="category",
        lazy="dynamic",
    )

    @property
    def published_post_count(self) -> int:
        """Return the number of published posts in this category."""
        return self.posts.filter_by(is_published=True).count()

    @property
    def text_color(self) -> str:
        """
        Return a contrasting text colour (black or white) for the category
        badge, based on the background colour's perceived luminance.
        """
        hex_color = self.color.lstrip("#")
        try:
            r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#000000" if luminance > 0.5 else "#ffffff"
        except (ValueError, IndexError):
            return "#ffffff"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "post_count": self.published_post_count,
        }

    def __repr__(self) -> str:
        return f"<Category {self.name!r}>"
