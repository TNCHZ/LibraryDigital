from library_digital.extensions import db

class CategoryBook(db.Model):
    __tablename__ = "category_book"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id", ondelete="CASCADE"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id", ondelete="CASCADE"), nullable=False)