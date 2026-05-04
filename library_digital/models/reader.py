from library_digital.extensions import db
from .base import BaseModel

class Reader(BaseModel):
    __tablename__ = "reader"

    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
