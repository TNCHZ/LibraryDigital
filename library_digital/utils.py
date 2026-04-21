from datetime import timedelta
from library_digital.extensions import db
from library_digital.models import User, Book, Category, CategoryBook, BorrowSlip
from library_digital.models.user import GenderEnum
from library_digital.models.borrow_slip import BorrowStatus
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

def update_user_profile(user, first_name, last_name, email, phone, gender):
    if not all([first_name, last_name, email, phone, gender]):
        return False, "Vui lòng nhập đầy đủ thông tin!"
    if User.query.filter(User.email == email, User.id != user.id).first():
        return False, "Email đã tồn tại!"
    if User.query.filter(User.phone == phone, User.id != user.id).first():
        return False, "Số điện thoại đã tồn tại!"

    try:
        gender_enum = GenderEnum(gender)
    except ValueError:
        return False, "Giới tính không hợp lệ!"

    try:
        # update
        user.first_name = first_name.strip()
        user.last_name = last_name.strip()
        user.email = email.strip()
        user.phone = phone.strip()
        user.gender = gender_enum

        db.session.commit()
        return True, "Cập nhật thành công!"

    except Exception as e:
        db.session.rollback()
        print(e)
        return False, "Có lỗi xảy ra!"

def change_user_password(user, current_password, new_password, confirm_password):
    current_password_hashed = str(hashlib.md5(current_password.strip().encode('utf-8')).hexdigest())

    if user.password != current_password_hashed:
        return False, "Mật khẩu hiện tại không đúng!"
    if new_password != confirm_password:
        return False, "Mật khẩu xác nhận không khớp!"

    try:
        new_password_hashed = str(hashlib.md5(new_password.strip().encode('utf-8')).hexdigest())

        user.password = new_password_hashed
        db.session.commit()

        return True, "Đổi mật khẩu thành công!"

    except Exception as e:
        db.session.rollback()
        print(e)
        return False, "Có lỗi xảy ra!"

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


def get_category_by_id(category_id):
    return Category.query.get(category_id)


def add_book(title, description, publisher, published_date, price, author, isbn_10, isbn_13, image, language, category_ids, librarian_id=None):
    book = Book(
        title=title.strip(),
        description=description.strip(),
        publisher=publisher.strip(),
        published_date=published_date,
        price=price,
        author=author.strip(),
        isbn_10=isbn_10.strip() if isbn_10 else None,
        isbn_13=isbn_13.strip() if isbn_13 else None,
        image=image,
        is_active=True,
        language=language.strip() if language else None,
        librarian_id=librarian_id
    )

    db.session.add(book)
    db.session.flush()  # Get book.id without committing

    # Add categories
    if category_ids:
        for cat_id in category_ids:
            category = get_category_by_id(cat_id)
            if category:
                book.categories.append(category)

    db.session.commit()
    return book


def update_book(book_id, title=None, description=None, publisher=None, published_date=None, price=None,
                author=None, isbn_10=None, isbn_13=None, image=None, language=None, is_active=None, category_ids=None):
    book = get_book_by_id(book_id)
    if not book:
        return None

    if title is not None:
        book.title = title.strip()
    if description is not None:
        book.description = description.strip()
    if publisher is not None:
        book.publisher = publisher.strip()
    if published_date is not None:
        book.published_date = published_date
    if price is not None:
        book.price = price
    if author is not None:
        book.author = author.strip()
    if isbn_10 is not None:
        book.isbn_10 = isbn_10.strip() if isbn_10 else None
    if isbn_13 is not None:
        book.isbn_13 = isbn_13.strip() if isbn_13 else None
    if image is not None:
        book.image = image
    if language is not None:
        book.language = language.strip() if language else None
    if is_active is not None:
        book.is_active = is_active

    # Update categories
    if category_ids is not None:
        book.categories = []
        for cat_id in category_ids:
            category = get_category_by_id(cat_id)
            if category:
                book.categories.append(category)

    db.session.commit()
    return book


def delete_book(book_id):
    book = get_book_by_id(book_id)
    if not book:
        return False

    db.session.delete(book)
    db.session.commit()
    return True


def add_borrow_slip(reader_id, librarian_id, book_id, borrow_date, due_date, return_date, status, note):
    try:
        # Nếu status truyền vào là string thì convert sang Enum
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

    book = Book.query.get(book_id)

    if not book:
        return False, "Sách không thấy"

    if book.quantity <= 0:
        return False, "Sách đã hết"

    if not latest_slip:
        return True, "OK"
        
    if latest_slip.status == BorrowStatus.BORROWING or latest_slip.status == BorrowStatus.RESERVED:
        return False, "Đang mượn sách"

    return True, "OK"


def get_borrow_slips(status=None, page=1, per_page=10):
    """Get borrow slips with optional status filter and pagination"""
    query = BorrowSlip.query
    if status:
        query = query.filter(BorrowSlip.status == BorrowStatus(status))
    query = query.order_by(BorrowSlip.created_at.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_borrow_slip_by_id(slip_id):
    """Get a single borrow slip by ID"""
    return BorrowSlip.query.get(slip_id)


def approve_borrow_slip(slip_id, librarian_id):
    """Approve a borrow slip - change status from RESERVED to BORROWING"""
    try:
        slip = get_borrow_slip_by_id(slip_id)
        if not slip:
            return False, "Không tìm thấy đơn mượn"
        
        if slip.status != BorrowStatus.RESERVED:
            return False, "Đơn mượn không ở trạng thái chờ duyệt"
        
        from datetime import datetime
        slip.status = BorrowStatus.BORROWING
        slip.librarian_id = librarian_id
        slip.borrow_date = datetime.now()
        slip.due_date = slip.borrow_date + timedelta(days=30)
        
        db.session.commit()
        return True, "Duyệt đơn mượn thành công"
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"


def reject_borrow_slip(slip_id, librarian_id, note=None):
    """Reject a borrow slip - change status to REJECT"""
    try:
        slip = get_borrow_slip_by_id(slip_id)
        if not slip:
            return False, "Không tìm thấy đơn mượn"
        
        if slip.status not in [BorrowStatus.RESERVED, BorrowStatus.BORROWING]:
            return False, "Không thể từ chối đơn mượn này"
        
        slip.status = BorrowStatus.REJECT
        slip.librarian_id = librarian_id
        if note:
            slip.note = note if not slip.note else f"{slip.note}\n[Từ chối]: {note}"
        
        db.session.commit()
        return True, "Từ chối đơn mượn thành công"
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"
