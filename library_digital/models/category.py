from library_digital.extensions import db
from .base import BaseModel

class Category(BaseModel):
    __tablename__ = "category"

    name = db.Column(db.String(255), nullable=False)