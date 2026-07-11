from datetime import datetime

from database import db


class Movie(db.Model):
    __tablename__ = "movies"
    __table_args__ = (
        db.CheckConstraint("rating >= 0 and rating <= 10", name="rating_range"),
        db.CheckConstraint("duration > 0", name="duration_positive"),
        db.CheckConstraint("release_year >= 1888", name="release_year_valid"),
        db.CheckConstraint(
            "status IN ('Watching', 'Completed', 'Plan to Watch', 'Dropped')",
            name="status_valid",
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    STATUSES = ("Watching", "Completed", "Plan to Watch", "Dropped")

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    genre = db.Column(db.String(100), nullable=False, index=True)
    release_year = db.Column(db.Integer, nullable=False, index=True)
    duration = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False, index=True)
    poster_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Movie id={self.id} title={self.title!r}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "genre": self.genre,
            "release_year": self.release_year,
            "duration": self.duration,
            "rating": self.rating,
            "poster_url": self.poster_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
