from library_digital.extensions import db
from library_digital.models import User, Book, Category, CategoryBook
import hashlib


def add_user(first_name, last_name, username, password, email, phone, gender, **kwargs):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

    user = User(first_name=first_name.strip(),
                last_name=last_name.strip(),
                username=username.strip(),
                password=password,
                phone=phone.strip(),
                email=email.strip(),
                gender=gender,
                avatar=kwargs.get('avatar'))

    db.session.add(user)
    db.session.commit()


def check_login(username, password, role):
    if username and password and role:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.username.__eq__(username.strip()), User.password.__eq__(password), User.role.__eq__(role)).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_books():
    return Book.query.all()

def get_book_by_id(book_id):
    return Book.query.get(book_id)

def get_categories():
    return Category.query.all()

def get_books_by_category(category_id):
    return Book.query.join(CategoryBook).filter(CategoryBook.category_id == category_id).all()


def search_books(isbn_10=None, isbn_13=None, title=None, author=None, category_ids=None, page=1, per_page=8):
    query = Book.query

    if isbn_10:
        query = query.filter(Book.isbn_10.ilike(f'%{isbn_10}%'))
    
    if isbn_13:
        query = query.filter(Book.isbn_13.ilike(f'%{isbn_13}%'))

    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))

    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))

    if category_ids:
        query = query.join(CategoryBook).filter(CategoryBook.category_id.in_(category_ids))

    return query.paginate(page=page, per_page=per_page, error_out=False)
