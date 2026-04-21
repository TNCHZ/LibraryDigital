from library_digital.extensions import db
from .base import BaseModel
import enum

class BorrowStatus(enum.Enum):
    BORROWING = "BORROWING"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"
    LOST = "LOST"
    RESERVED = "RESERVED"
    DAMAGED = "DAMAGED"

class BorrowSlip(BaseModel):
    __tablename__ = "borrow_slip"

    reader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    librarian_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    borrow_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)

    status = db.Column(db.Enum(BorrowStatus), nullable=False)

    note = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
