from library_digital.extensions import db
from .base import BaseModel

class Admin(BaseModel):
    __tablename__ = "admin"

    id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)