from library_digital.extensions import db
from .base import BaseModel

class Librarian(BaseModel):
    __tablename__ = "librarian"

    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    start_date = db.Column(db.DateTime, nullable=False)