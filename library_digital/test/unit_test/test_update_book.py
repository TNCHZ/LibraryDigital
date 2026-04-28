from unittest.mock import patch, MagicMock
import pytest
from library_digital.utils import update_book


class FakeCategory:
    def __init__(self, id):
        self.id = id


class FakeBook:
    def __init__(self):
        self.title = "Old title"
        self.description = "Old desc"
        self.publisher = "Old pub"
        self.published_date = 2000
        self.price = 100
        self.author = "Old author"
        self.isbn_10 = None
        self.isbn_13 = None
        self.image = "old.jpg"
        self.language = "vi"
        self.is_active = False
        self.categories = []

# TEST CẬP NHẬT SÁCH THÀNH CÔNG
@patch('library_digital.utils.db.session.commit')
@patch('library_digital.utils.get_category_by_id')
@patch('library_digital.utils.get_book_by_id')
def test_update_book_success(mock_get_book, mock_get_category, mock_commit):

    # fake book
    mock_book = FakeBook()
    mock_get_book.return_value = mock_book

    # fake category
    mock_get_category.return_value = FakeCategory(1)

    result = update_book(
        book_id=1,
        title="New title",
        description="New desc",
        publisher="New pub",
        published_date=2024,
        price=200,
        author="New author",
        isbn_10="123",
        isbn_13="456",
        image="new.jpg",
        language="en",
        is_active=True,
        category_ids=[1, 2]
    )

    assert result is not None

    assert mock_book.title == "New title"
    assert mock_book.description == "New desc"
    assert mock_book.publisher == "New pub"
    assert mock_book.published_date == 2024
    assert mock_book.price == 200
    assert mock_book.author == "New author"
    assert mock_book.image == "new.jpg"
    assert mock_book.language == "en"
    assert mock_book.is_active is True

    # categories updated
    assert len(mock_book.categories) == 2

    mock_commit.assert_called_once()