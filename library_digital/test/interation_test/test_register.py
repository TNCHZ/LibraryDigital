import pytest
import json
from unittest.mock import patch
import io
from pathlib import Path
from library_digital.models.user import User

from library_digital.index import app
from library_digital.extensions import db


def load_data():
    path = Path(__file__).resolve().parents[2] / 'data' / 'data_test.json'
    return json.loads(path.read_text(encoding='utf-8'))


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
        yield app.test_client()
        db.session.remove()

# TEST ĐĂNG KÝ
@patch('cloudinary.uploader.upload')
def test_register_from_json(mock_upload, client):
    data = load_data()

    mock_upload.return_value = {
        'secure_url': 'http://fake-url/avatar.png'
    }

    for u in data['user']:
        response = client.post('/auth/register', data={
            'first_name': 'Test',
            'last_name': f"User{u['id']}",
            'username': u['username'],
            'password': u['password'],
            'confirm_password': u['password'],
            'email': u['email'],
            'phone': f"09{u['id']:08d}",
            'gender': 'MALE',
            'avatar': (io.BytesIO(b"fake image"), 'avatar.png')
        }, content_type='multipart/form-data')

        assert response.status_code == 302

        user = User.query.filter_by(username=u['username']).first()
        assert user is not None
        assert user.email == u['email']
        assert user.avatar == 'http://fake-url/avatar.png'

# TEST ĐĂNG KÝ TRÙNG LẶP
@patch('cloudinary.uploader.upload')
def test_register_duplicate(mock_upload, client):
    data = load_data()
    u = data['user'][0]

    mock_upload.return_value = {
        'secure_url': 'http://fake-url/avatar.png'
    }

    # đăng ký lần 1
    client.post('/auth/register', data={
        'first_name': 'Test',
        'last_name': 'User',
        'username': u['username'],
        'password': u['password'],
        'confirm_password': u['password'],
        'email': u['email'],
        'phone': '0123456789',
        'gender': 'MALE',
        'avatar': (io.BytesIO(b"fake image"), 'avatar.png')
    }, content_type='multipart/form-data')

    # đăng ký lại
    response = client.post('/auth/register', data={
        'first_name': 'Test',
        'last_name': 'User',
        'username': u['username'],
        'password': u['password'],
        'confirm_password': u['password'],
        'email': u['email'],
        'phone': '0123456789',
        'gender': 'MALE',
        'avatar': (io.BytesIO(b"fake image"), 'avatar.png')
    }, content_type='multipart/form-data')

    assert response.status_code == 200