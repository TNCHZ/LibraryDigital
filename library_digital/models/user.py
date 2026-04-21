from email.policy import default

from library_digital.extensions import db
from .base import BaseModel
import enum
from flask_login import UserMixin

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    LIBRARIAN = "LIBRARIAN"
    READER = "READER"

class GenderEnum(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class User(BaseModel, UserMixin):
    __tablename__ = "user"

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    gender = db.Column(db.Enum(GenderEnum), nullable=False)
    avatar = db.Column(db.String(255))

    role = db.Column(db.Enum(UserRole), default=UserRole.READER, nullable=False)

    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    is_active = db.Column(db.Boolean, default=True)

    # relationships
    books_managed = db.relationship("Book", backref="librarian", lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name