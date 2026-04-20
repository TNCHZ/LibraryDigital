from library_digital.extensions import db
from .base import BaseModel


class Book(BaseModel):
    __tablename__ = "book"

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publisher = db.Column(db.String(255), nullable=False)
    published_date = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    author = db.Column(db.String(255), nullable=False)

    isbn_10 = db.Column(db.String(10))
    isbn_13 = db.Column(db.String(13))

    image = db.Column(db.String(255), nullable=False)

    quantity = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, nullable=False)

    language = db.Column(db.String(50))

    librarian_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    categories = db.relationship("Category", secondary="category_book", backref="books")
