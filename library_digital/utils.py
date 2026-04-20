from OpenSSL.rand import status

from library_digital.extensions import db
from library_digital.models import User, Book, Category, CategoryBook, BorrowSlip
import hashlib

from library_digital.models.borrow_slip import BorrowStatus


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

def add_borrow_slip(reader_id, librarian_id, book_id,borrow_date, due_date, return_date, status, note):
    try:
        if isinstance(status, str):
            status = BorrowStatus(status)

        borrow_slip = BorrowSlip(
            reader_id=reader_id,
            librarian_id=librarian_id,
            book_id=book_id,
            borrow_date=borrow_date,
            due_date=due_date,
            return_date=return_date,
            status=status,
            note=note
        )

        db.session.add(borrow_slip)
        db.session.commit()

        return borrow_slip

    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return None

def can_borrow(reader_id, book_id):
    latest_slip = BorrowSlip.query \
        .filter_by(reader_id=reader_id) \
        .order_by(BorrowSlip.borrow_date.desc()) \
        .first()

    print(latest_slip)

    if not latest_slip:
        return True, "OK"

    book = Book.query.get(book_id)

    if latest_slip.status == BorrowStatus.BORROWING or latest_slip.status == BorrowStatus.RESERVED:
        return False, "Độc giả chưa trả sách"

    if not book:
        return False, "Không tìm thấy sách"

    if book.quantity <= 0:
        return False, "Sách đã hết"



    return True, "OK"