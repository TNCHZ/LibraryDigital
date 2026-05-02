import pytest

from library_digital.index import app
from library_digital.extensions import db
from library_digital.models import User, Book
from library_digital.models.user import UserRole, GenderEnum


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

        book1 = Book(
            id=1,
            title="Book 1",
            description="Desc",
            publisher="NXB",
            published_date=2020,
            price=100000,
            quantity=5,
            author="Author",
            is_active=True,
            image="test.jpg",
            librarian_id=2
        )

        book2 = Book(
            id=2,
            title="Book 2",
            description="Desc",
            publisher="NXB",
            published_date=2021,
            price=120000,
            quantity=5,
            author="Author",
            is_active=True,
            image="test.jpg",
            librarian_id=2
        )

        db.session.add_all([book1, book2])
        db.session.commit()

        yield app.test_client()

        db.session.remove()



def login_librarian(client):
    with client.session_transaction() as sess:
        sess["_user_id"] = "2"
        sess["_fresh"] = True



# TEST DELETE SÁCH THÀNH CÔNG
def test_delete_book_success(client):
    login_librarian(client)

    response = client.post("/librarian/book/delete/1/")

    assert response.status_code == 302

    with app.app_context():
        book = Book.query.get(1)
        assert book is None

        # đảm bảo book khác vẫn còn
        assert Book.query.get(2) is not None



# TEST DELETE KHÔNG TỒN TẠI
def test_delete_book_not_found(client):
    login_librarian(client)

    response = client.post("/librarian/book/delete/999/")

    assert response.status_code == 404



# TEST KHÔNG LOGIN
def test_delete_book_without_login(client):
    response = client.post("/librarian/book/delete/1/")

    # tùy hệ thống bạn → có thể redirect login
    assert response.status_code in (302, 401, 403)


# TEST DELETE NHIỀU LẦN
def test_delete_book_twice(client):
    login_librarian(client)

    response1 = client.post("/librarian/book/delete/1/")
    assert response1.status_code == 302

    response2 = client.post("/librarian/book/delete/1/")
    assert response2.status_code == 404