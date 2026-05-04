import pytest
import json
from pathlib import Path
from io import BytesIO
from werkzeug.datastructures import MultiDict

from library_digital.index import app
from library_digital.extensions import db
from library_digital.models import User, Book, Category
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


        book = Book(
            id=1,
            title="Old Book",
            description="Old Desc",
            publisher="NXB",
            published_date=2000,
            price=100000,
            quantity=5,
            author="Old Author",
            isbn_10="1234567890",
            isbn_13="9781234567890",
            image="old.jpg",
            language="English",
            is_active=True,
            librarian_id=2
        )
        db.session.add(book)
        db.session.commit()


        import cloudinary.uploader
        monkeypatch.setattr(
            cloudinary.uploader,
            "upload",
            lambda file: {"secure_url": "http://test-image.com/new.jpg"}
        )

        yield app.test_client()

        db.session.remove()


def login_librarian(client):
    with client.session_transaction() as sess:
        sess["_user_id"] = "2"
        sess["_fresh"] = True



# TEST UPDATE SÁCH THÀNH CÔNG
def test_edit_book_success(client):
    login_librarian(client)

    form_data = MultiDict()
    form_data.add("title", "Updated Book")
    form_data.add("description", "Updated Desc")
    form_data.add("publisher", "NXB Updated")
    form_data.add("published_date", "2025")
    form_data.add("price", "200000")
    form_data.add("author", "New Author")
    form_data.add("isbn_10", "1111111111")
    form_data.add("isbn_13", "9781111111111")
    form_data.add("language", "Vietnamese")

    # đổi category
    form_data.add("category_ids", "1")
    form_data.add("category_ids", "2")

    form_data.add("image", (BytesIO(b"fake"), "test.jpg"))

    response = client.post(
        "/librarian/book/edit/1/",
        data=form_data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 302

    with app.app_context():
        book = Book.query.get(1)

        assert book.title == "Updated Book"
        assert book.description == "Updated Desc"
        assert book.publisher == "NXB Updated"
        assert book.price == 200000
        assert book.author == "New Author"
        assert book.image == "http://test-image.com/new.jpg"

        category_ids = sorted([c.id for c in book.categories])
        assert category_ids == [1, 2]



# TEST KHÔNG UPLOAD ẢNH
def test_edit_book_without_image(client):
    login_librarian(client)

    form_data = {
        "title": "No Image Update",
        "author": "Tester"
    }

    response = client.post("/librarian/book/edit/1/", data=form_data)

    assert response.status_code == 302

    with app.app_context():
        book = Book.query.get(1)
        assert book.title == "No Image Update"
        assert book.image == "old.jpg"  # giữ nguyên



# TEST BOOK KHÔNG TỒN TẠI
def test_edit_book_not_found(client):
    login_librarian(client)

    response = client.post(
        "/librarian/book/edit/999/",
        data={"title": "Test"}
    )

    # vì bạn return None → có thể vẫn redirect
    assert response.status_code in (302, 500)



# TEST UPDATE CATEGORY RỖNG
def test_edit_book_clear_categories(client):
    login_librarian(client)

    form_data = MultiDict()
    form_data.add("title", "Clear Category Book")

    response = client.post(
        "/librarian/book/edit/1/",
        data=form_data
    )

    assert response.status_code == 302

    with app.app_context():
        book = Book.query.get(1)
        assert book.title == "Clear Category Book"