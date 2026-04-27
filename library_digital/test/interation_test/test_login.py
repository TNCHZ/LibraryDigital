import pytest
import json
import hashlib
from pathlib import Path

from library_digital.index import app
from library_digital.extensions import db
from library_digital.models.user import User, UserRole, GenderEnum


def md5_hash(password):
    return hashlib.md5(password.encode('utf-8')).hexdigest()


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
        data = load_data()

        admin_ids = {a['id'] for a in data['admin']}
        librarian_ids = {l['id'] for l in data['librarian']}

        for u in data['user']:
            if u['id'] in admin_ids:
                role = UserRole.ADMIN
            elif u['id'] in librarian_ids:
                role = UserRole.LIBRARIAN
            else:
                role = UserRole.READER

            user = User(
                id=u['id'],
                username=u['username'],
                password=md5_hash(u['password']),
                email=u['email'],
                first_name="Test",
                last_name=f"User{u['id']}",
                phone=f"09{u['id']:08d}",
                gender=GenderEnum.MALE.value,
                role=role.value,
                is_active=True
            )
            db.session.add(user)

        db.session.commit()

        yield app.test_client()

        db.session.remove()

# TEST ĐĂNG NHẬP ADMIN
def test_login_admin_success(client):
    response = client.post('/auth/login', data={
        'username': 'user1',
        'password': '123456',
        'role': 'ADMIN'
    })

    assert response.status_code == 302
    assert '/admin' in response.headers['Location']

# TEST ĐĂNG NHẬP LIBRARIAN
def test_login_librarian_success(client):
    response = client.post('/auth/login', data={
        'username': 'user2',
        'password': '123456',
        'role': 'LIBRARIAN'
    })

    assert response.status_code == 302
    assert '/librarian' in response.headers['Location']

# TEST ĐĂNG NHẬP READER
def test_login_reader_success(client):
    response = client.post('/auth/login', data={
        'username': 'user3',
        'password': '123456',
        'role': 'READER'
    })

    assert response.status_code == 302
    assert '/' in response.headers['Location']

# TEST ĐĂNG NHẬP SAI MẬT KHẨU
def test_login_wrong_password(client):
    response = client.post('/auth/login', data={
        'username': 'user1',
        'password': 'wrongpass',
        'role': 'ADMIN'
    })

    assert response.status_code in (200, 401)

# TEST ĐĂNG NHẬP KHÔNG TÌM THẤY TÀI KHOẢN
def test_login_user_not_found(client):
    response = client.post('/auth/login', data={
        'username': 'not_exist',
        'password': '123456',
        'role': 'ADMIN'
    })

    assert response.status_code in (200, 401)

# TEST ĐĂNG NHẬP SAI VAI TRÒ
def test_login_wrong_role(client):
    response = client.post('/auth/login', data={
        'username': 'user1',
        'password': '123456',
        'role': 'READER'
    })

    assert response.status_code in (200, 403)
