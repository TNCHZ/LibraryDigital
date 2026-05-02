from datetime import datetime

from library_digital.extensions import db

class ReaderCategory(db.Model):
    __tablename__ = "reader_category"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="reader_categories")
    category = db.relationship("Category", backref="reader_categories")
