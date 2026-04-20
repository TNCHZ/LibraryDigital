from library_digital.extensions import db
from .base import BaseModel

class CategoryBook(BaseModel):
    __tablename__ = "category_book"

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)