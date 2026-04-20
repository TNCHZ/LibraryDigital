from library_digital.extensions import db
from .base import BaseModel

class ReaderCategory(BaseModel):
    __tablename__ = "reader_category"

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)