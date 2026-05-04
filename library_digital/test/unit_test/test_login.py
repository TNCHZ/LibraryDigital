import pytest
from unittest.mock import patch
from flask_login import UserMixin
from flask import url_for

from library_digital.index import app
from library_digital.models.user import UserRole


# Fake User chuẩn Flask-Login
class FakeUser(UserMixin):
    def __init__(self, user_id=1, role=UserRole.READER):
        self.id = user_id
        self.role = role

    @property
    def is_active(self):
        return True

# Flask test_unit client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_unit'

    with app.test_client() as client:
        yield client

# TEST LOGIN ADMIN
@patch('library_digital.utils.check_login')
def test_login_success_admin(mock_check_login, client):

    mock_check_login.return_value = FakeUser(
        user_id=1,
        role=UserRole.ADMIN
    )

    response = client.post('/auth/login', data={
        'username': 'admin',
        'password': '123456',
        'role': 'ADMIN'
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith(url_for('admin_dashboard'))

# TEST LOGIN LIBRARIAN
@patch('library_digital.utils.check_login')
def test_login_success_librarian(mock_check_login, client):

    mock_check_login.return_value = FakeUser(
        user_id=2,
        role=UserRole.LIBRARIAN
    )

    response = client.post('/auth/login', data={
        'username': 'lib',
        'password': '123456',
        'role': 'LIBRARIAN'
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith(url_for('librarian_dashboard'))

# TEST LOGIN READER
@patch('library_digital.utils.check_login')
def test_login_success_reader(mock_check_login, client):

    mock_check_login.return_value = FakeUser(
        user_id=3,
        role=UserRole.READER
    )

    response = client.post('/auth/login', data={
        'username': 'user',
        'password': '123456',
        'role': 'READER'
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith(url_for('home'))

# TEST LOGIN THẤT BẠI VÌ SAI TÀI KHOẢN MẬT KHẨU
@patch('library_digital.utils.check_login')
def test_login_fail(mock_check_login, client):

    mock_check_login.return_value = None

    response = client.post('/auth/login', data={
        'username': 'wrong',
        'password': 'wrong',
        'role': 'READER'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Sai tài khoản hoặc mật khẩu" in response.get_data(as_text=True)

# TEST LOGIN THẤT BẠI VÌ SAI ROLE
@patch('library_digital.utils.check_login')
def test_login_invalid_role(mock_check_login, client):

    mock_check_login.return_value = None

    response = client.post('/auth/login', data={
        'username': 'user1',
        'password': '123456',
        'role': 'INVALID'
    })

    assert response.status_code == 200