from sqlalchemy import UniqueConstraint

from library_digital.extensions import db
from .base import BaseModel

class ViewHistory(BaseModel):
    __tablename__ = "view_history"

    count = db.Column(db.Integer, nullable=False)
    reader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)

    reader = db.relationship("User", foreign_keys=[reader_id], backref="view_history")
    book = db.relationship("Book", backref="view_history")

    __table_args__ = (
        UniqueConstraint('reader_id', 'book_id', name='unique_reader_book'),
    )

