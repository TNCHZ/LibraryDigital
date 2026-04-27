import pytest
from unittest.mock import patch
from library_digital.index import app


# Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'

    with app.test_client() as client:
        yield client



# TEST REGISTER THÀNH CÔNG
@patch('library_digital.utils.add_user')
@patch('cloudinary.uploader.upload')
def test_register_success(mock_upload, mock_add_user, client):
    mock_upload.return_value = {
        'secure_url': 'http://test-avatar.jpg'
    }

    response = client.post('/auth/register', data={
        'first_name': 'Tuan',
        'last_name': 'Kieu',
        'username': 'testuser',
        'password': '123456',
        'confirm_password': '123456',
        'phone': '0123456789',
        'email': 'test@gmail.com',
        'gender': 'MALE'
    })

    # Kiểm tra redirect
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

    # Kiểm tra add_user được gọi
    mock_add_user.assert_called_once()



# TEST PASSWORD KHÔNG KHỚP
@patch('library_digital.utils.add_user')
def test_register_password_not_match(mock_add_user, client):
    response = client.post('/auth/register', data={
        'first_name': 'Tuan',
        'last_name': 'Kieu',
        'username': 'testuser',
        'password': '123456',
        'confirm_password': '654321',
        'phone': '0123456789',
        'email': 'test@gmail.com',
        'gender': 'MALE'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Mật khẩu không khớp" in response.get_data(as_text=True)

    # Không được gọi add_user
    mock_add_user.assert_not_called()


# TEST LỖI EXCEPTION
@patch('library_digital.utils.add_user')
def test_register_exception(mock_add_user, client):
    mock_add_user.side_effect = Exception("DB lỗi")

    response = client.post('/auth/register', data={
        'first_name': 'Tuan',
        'last_name': 'Kieu',
        'username': 'testuser',
        'password': '123456',
        'confirm_password': '123456',
        'phone': '0123456789',
        'email': 'test@gmail.com',
        'gender': 'MALE'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Hệ thống đang gặp lỗi" in response.get_data(as_text=True)