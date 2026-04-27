import pytest
from datetime import date
import hashlib

from library_digital.index import app
from library_digital.extensions import db
from library_digital.models import User, Book, BorrowSlip

def md5_hash(password):
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def clean_db():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


@pytest.fixture
def client():
    with app.app_context():
        db.create_all()
        clean_db()

        user = User(
            id=1,
            username="lib1",
            password=md5_hash('123456'),
            email="lib@gmail.com",
            first_name="Lib",
            last_name="User",
            phone="0123456789",
            gender="MALE",
            role="READER",
            avatar="http://fake-url/avatar.png",
            is_active=True
        )
        db.session.add(user)

        book = Book(
            id=1,
            title="Book 1",
            description="Test description",
            publisher="NXB Test",
            published_date=2024,
            price=100000,
            author="Author 1",
            isbn_10="1234567890",
            isbn_13="9781234567890",
            image="http://test-image.com/book.png",
            quantity=5,
            is_active=True,
            language="Vietnamese",
            librarian_id=1
        )
        db.session.add(book)

        slip = BorrowSlip(
            id=1,
            reader_id=1,
            librarian_id=None,
            book_id=1,  # 🔥 QUAN TRỌNG
            borrow_date=date(2026, 1, 1),
            due_date=date(2026, 1, 10),
            return_date=None,
            status="BORROWING",  # 🔥 FIX ENUM
            note=None,
            is_active=True
        )
        db.session.add(slip)

        db.session.commit()
        yield app.test_client()
        db.session.remove()

# TEST XEM LỊCH SỬ MƯỢN SÁCH
def test_borrow_history_success(client):
    response = client.get('/user/1/borrow-history')

    assert response.status_code == 200

    html = response.data.decode("utf-8")

    assert "Book 1" in html
    assert "2026" in html

# TEST DANH SÁCH TRỐNG
def test_borrow_history_empty(client):
    response = client.get('/user/999/borrow-history')

    assert response.status_code == 200

    html = response.data.decode("utf-8")

    assert "Book 1" not in html
