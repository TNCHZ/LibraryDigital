import pytest
import json
from pathlib import Path
from io import BytesIO
from werkzeug.datastructures import MultiDict

from library_digital.index import app
from library_digital.extensions import db
from library_digital.models import User, Category, Book
from library_digital.models.user import UserRole, GenderEnum

def load_data():
    path = Path(__file__).resolve().parents[2] / 'data' / 'data_test.json'
    return json.loads(path.read_text(encoding='utf-8'))


def clean_db():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()

@pytest.fixture
def client(monkeypatch):
    with app.app_context():
        db.create_all()
        clean_db()
        data = load_data()

        librarian = User(
            id=2,
            username="librarian",
            password="123456",
            email="lib@test.com",
            first_name="Lib",
            last_name="User",
            phone="0900000000",
            gender=GenderEnum.MALE.value,
            role=UserRole.LIBRARIAN.value,
            is_active=True
        )
        db.session.add(librarian)

        for c in data['category']:
            db.session.add(Category(id=c['id'], name=c['name']))

        db.session.commit()

        import cloudinary.uploader
        monkeypatch.setattr(
            cloudinary.uploader,
            "upload",
            lambda file: {"secure_url": "http://test-image.com/test.jpg"}
        )

        yield app.test_client()
        db.session.remove()

def login_librarian(client):
    with client.session_transaction() as sess:
        sess["_user_id"] = "2"
        sess["_fresh"] = True


# TEST THÊM SÁCH THÀNH CÔNG
def test_add_books_from_sample_data(client):
    login_librarian(client)

    data = load_data()

    for b in data['book']:
        category_ids = [
            str(cb["category_id"])
            for cb in data["category_book"]
            if cb["book_id"] == b["id"]
        ]

        form_data = MultiDict()

        form_data.add("title", b["title"])
        form_data.add("description", b["description"])
        form_data.add("publisher", b["publisher"])
        form_data.add("published_date", str(b["published_date"]))  # 🔥 fix
        form_data.add("price", str(b["price"]))  # 🔥 fix
        form_data.add("author", b["author"])
        form_data.add("isbn_10", b["isbn_10"])
        form_data.add("isbn_13", b["isbn_13"])
        form_data.add("language", b["language"])

        for cid in category_ids:
            form_data.add("category_ids", cid)

        form_data.add("image", (BytesIO(b"fake image"), "test.jpg"))

        response = client.post(
            "/librarian/book/add/",
            data=form_data,
            content_type="multipart/form-data"
        )

        assert response.status_code == 302, response.data.decode()

# TEST THÊM SÁCH KHÔNG THÀNH CÔNG
def test_add_book_missing_required_field(client):
    login_librarian(client)

    response = client.post("/librarian/book/add/", data={
        "title": "",
        "author": "Tester"
    })

    assert response.status_code in (400, 500)

    with app.app_context():
        book = Book.query.filter_by(author="Tester").first()
        assert book is None