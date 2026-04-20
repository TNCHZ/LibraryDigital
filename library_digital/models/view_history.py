from library_digital.extensions import db
from .base import BaseModel

class ViewHistory(BaseModel):
    __tablename__ = "view_history"

    count = db.Column(db.Integer, nullable=False)