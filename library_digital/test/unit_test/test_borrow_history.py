import pytest
from datetime import date
from unittest.mock import patch
from library_digital.index import app

class FakeBook:
    def __init__(self, title, image=""):
        self.title = title
        self.image = image


class FakeStatus:
    def __init__(self, value):
        self.value = value


class FakeSlip:
    def __init__(self, book_id, title, status):
        self.book_id = book_id
        self.book = FakeBook(title)
        self.borrow_date = date(2026, 4, 20)
        self.due_date = date(2026, 4, 27)
        self.status = FakeStatus(status)


# Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_unit'

    with app.test_client() as client:
        yield client


# TEST XEM LỊCH SỬ SÁCH THÀNH CÔNG
@patch('library_digital.utils.get_reserved_slip_by_reader')
def test_borrow_status_success(mock_get_slip, client):

    mock_get_slip.return_value = FakeSlip(
        book_id=1,
        title="Book 1",
        status="RESERVED"
    )

    user_id = 3

    response = client.get(f'/user/{user_id}/borrow-status')

    assert response.status_code == 200

    html = response.data.decode('utf-8')

    assert "Book 1" in html
    assert "Đang chờ" in html or "RESERVED" in html
    assert "Hủy yêu cầu" in html

    mock_get_slip.assert_called_once_with(user_id)


# TEST PHÂN TRANG THÀNH CÔNG
@patch('library_digital.utils.get_reserved_slip_by_reader')
def test_borrow_status_empty(mock_get_slip, client):

    mock_get_slip.return_value = None

    response = client.get('/user/3/borrow-status')

    assert response.status_code == 200

    html = response.data.decode('utf-8')

    assert "Hủy yêu cầu" not in html
    mock_get_slip.assert_called_once_with(3)
