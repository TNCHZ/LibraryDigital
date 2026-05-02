from unittest.mock import patch
import pytest
from io import BytesIO
from library_digital.index import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_unit'

    with app.test_client() as client:
        yield client


@patch('library_digital.utils.add_book')
@patch('cloudinary.uploader.upload')
def test_admin_add_book_success(mock_upload, mock_add_book, client):

    mock_upload.return_value = {
        'secure_url': 'http://fake-image.com/book.jpg'
    }

    mock_add_book.return_value = None

    data = {
        'title': 'Clean Code',
        'description': 'A book about clean code',
        'publisher': 'Prentice Hall',
        'published_date': 2020,
        'price': 100000,
        'author': 'Robert C. Martin',
        'isbn_10': '1234567890',
        'isbn_13': '1234567890123',
        'language': 'English',
        'category_ids': [1, 2],
        'image': (BytesIO(b"fake image content"), 'book.jpg')
    }

    response = client.post(
        '/admin/book/add/',
        data=data,
        content_type='multipart/form-data'
    )

    assert response.status_code == 302

    mock_add_book.assert_called_once()

    args, kwargs = mock_add_book.call_args

    assert kwargs['image'] == 'http://fake-image.com/book.jpg'

@patch('library_digital.utils.add_book')
@patch('cloudinary.uploader.upload')
def test_admin_add_book_without_image(mock_upload, mock_add_book, client):

    data = {
        'title': 'Book no image',
        'description': 'desc',
        'publisher': 'pub',
        'published_date': 2024,
        'price': 50000,
        'author': 'author',
        'category_ids': [1, 2]
    }

    response = client.post(
        '/admin/book/add/',
        data=data
    )

    assert response.status_code == 302

    mock_upload.assert_not_called()

    mock_add_book.assert_called_once()

    args, kwargs = mock_add_book.call_args

    assert kwargs['title'] == 'Book no image'
    assert kwargs['image'] == 'https://via.placeholder.com/300x400?text=No+Cover'