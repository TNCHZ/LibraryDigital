from library_digital.extensions import db
from library_digital.models import User, Book, Category, CategoryBook, BorrowSlip, ViewHistory, ReaderCategory
from library_digital.models.user import GenderEnum, UserRole
import hashlib
from datetime import timedelta
from sqlalchemy.orm import joinedload
import json
from library_digital.models.borrow_slip import BorrowStatus
from .gemini_service import call_ai


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


def add_book(title, description, publisher, published_date, price, quantity, author, isbn_10, isbn_13, image, language, category_ids, librarian_id=None):
    book = Book(
        title=title.strip(),
        description=description.strip(),
        publisher=publisher.strip(),
        published_date=published_date,
        price=price,
        quantity=quantity if quantity is not None else 0,
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


def update_book(book_id, title=None, description=None, publisher=None, published_date=None, price=None, quantity=None,
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
    if quantity is not None:
        book.quantity = quantity
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

    if latest_slip.status == BorrowStatus.BORROWING or latest_slip.status == BorrowStatus.RESERVED:
        return False, "Đang mượn sách"

    if not latest_slip:
        return True, "OK"

    return True, "OK"


def get_borrow_slips_by_reader(reader_id, page=1, per_page=5):
    query = BorrowSlip.query.filter_by(reader_id=reader_id).order_by(BorrowSlip.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items": list(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "has_next": bool(pagination.has_next),
        "has_prev": bool(pagination.has_prev)
    }

def get_reserved_slip_by_reader(reader_id):
    slip = BorrowSlip.query\
        .filter_by(reader_id=reader_id, status=BorrowStatus.RESERVED)\
        .order_by(BorrowSlip.id.desc())\
        .first()

    return slip

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

def get_user_stats():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()


    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users
    }


def get_users(role=None, is_active=None):
    query = User.query


    if role and role != "ALL":
        query = query.filter(User.role == UserRole[role])


    if is_active is not None:
        query = query.filter(User.is_active == is_active)


    return query.all()


def admin_add_user(first_name, last_name, username, password, email, phone, gender, role, **kwargs):
    password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()


    user = User(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        username=username.strip(),
        password=password,
        phone=phone.strip(),
        email=email.strip(),
        gender=gender,
        role=role,
        avatar=kwargs.get('avatar')
    )


    db.session.add(user)
    db.session.commit()


def update_user(user_id, first_name, last_name, username, email, phone, gender, role, is_active, password=None, avatar=None):
    user = User.query.get(user_id)


    if not user:
        return False


    user.first_name = first_name.strip()
    user.last_name = last_name.strip()
    user.username = username.strip()
    user.email = email.strip()
    user.phone = phone.strip()
    user.gender = gender
    user.role = role
    user.is_active = is_active


    # password optional
    if password:
        user.password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()


    # avatar optional
    if avatar:
        user.avatar = avatar


    db.session.commit()
    return True


def delete_user(user_id):
    user = User.query.get(user_id)


    if user:
        db.session.delete(user)
        db.session.commit()
        return True


    return False



def get_dashboard_statistics(ref_date=None):
    """Get comprehensive statistics for admin dashboard"""
    from datetime import datetime, timedelta


    if ref_date is None:
        ref_date = datetime.now()


    # User statistics
    total_users = User.query.count()
    new_users_this_month = User.query.filter(
        db.extract('month', User.created_at) == ref_date.month,
        db.extract('year', User.created_at) == ref_date.year
    ).count()


    # Book statistics
    total_books = Book.query.count()
    total_books_value = db.session.query(db.func.sum(Book.price)).scalar() or 0


    # Borrow statistics
    total_loans = BorrowSlip.query.count()


    # Status breakdown
    pending_loans = BorrowSlip.query.filter(BorrowSlip.status == BorrowStatus.RESERVED).count()
    active_loans = BorrowSlip.query.filter(BorrowSlip.status == BorrowStatus.BORROWING).count()
    overdue_loans = BorrowSlip.query.filter(BorrowSlip.status == BorrowStatus.OVERDUE).count()
    returned_loans = BorrowSlip.query.filter(BorrowSlip.status == BorrowStatus.RETURNED).count()


    # This month's loans
    current_month_loans = BorrowSlip.query.filter(
        db.extract('month', BorrowSlip.created_at) == ref_date.month,
        db.extract('year', BorrowSlip.created_at) == ref_date.year
    ).count()


    # Last 6 months loan trend (relative to ref_date)
    months = []
    loan_counts = []
    for i in range(5, -1, -1):
        month_date = ref_date - timedelta(days=30*i)
        count = BorrowSlip.query.filter(
            db.extract('month', BorrowSlip.created_at) == month_date.month,
            db.extract('year', BorrowSlip.created_at) == month_date.year
        ).count()
        months.append(f"T{month_date.month}")
        loan_counts.append(count)


    # Top borrowed books
    top_books = db.session.query(
        Book,
        db.func.count(BorrowSlip.id).label('borrow_count')
    ).join(BorrowSlip, Book.id == BorrowSlip.book_id) \
     .group_by(Book.id) \
     .order_by(db.desc('borrow_count')) \
     .limit(5).all()


    # Books by category
    category_stats = db.session.query(
        Category,
        db.func.count(Book.id).label('book_count')
    ).join(CategoryBook, Category.id == CategoryBook.category_id) \
     .join(Book, CategoryBook.book_id == Book.id) \
     .group_by(Category.id) \
     .order_by(db.desc('book_count')) \
     .limit(5).all()


    # Return rate calculation
    completed_loans = returned_loans + overdue_loans
    on_time_return_rate = (returned_loans / completed_loans * 100) if completed_loans > 0 else 0


    # Circulation rate (books currently borrowed / total books)
    circulation_rate = (active_loans / total_books * 100) if total_books > 0 else 0


    return {
        'total_users': total_users,
        'new_users_this_month': new_users_this_month,
        'total_books': total_books,
        'total_books_value': total_books_value,
        'total_loans': total_loans,
        'pending_loans': pending_loans,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'returned_loans': returned_loans,
        'current_month_loans': current_month_loans,
        'months': months,
        'loan_counts': loan_counts,
        'top_books': top_books,
        'category_stats': category_stats,
        'on_time_return_rate': round(on_time_return_rate, 1),
        'circulation_rate': round(circulation_rate, 1)
    }




def get_monthly_loan_stats(ref_date=None):
    """Get loan statistics by month for the last 12 months"""
    from datetime import datetime, timedelta


    if ref_date is None:
        ref_date = datetime.now()


    months = []
    loan_data = []
    return_data = []


    for i in range(11, -1, -1):
        date = ref_date - timedelta(days=30*i)
        month_label = f"T{date.month}"


        # Loans created this month
        loans = BorrowSlip.query.filter(
            db.extract('month', BorrowSlip.created_at) == date.month,
            db.extract('year', BorrowSlip.created_at) == date.year
        ).count()


        # Books returned this month
        returns = BorrowSlip.query.filter(
            BorrowSlip.status == BorrowStatus.RETURNED,
            db.extract('month', BorrowSlip.updated_at) == date.month,
            db.extract('year', BorrowSlip.updated_at) == date.year
        ).count()


        months.append(month_label)
        loan_data.append(loans)
        return_data.append(returns)


    return {
        'months': months,
        'loans': loan_data,
        'returns': return_data
    }




def get_top_readers(limit=5, ref_date=None):
    """Get top readers by number of books borrowed"""
    from sqlalchemy import func
    from datetime import datetime


    if ref_date is None:
        ref_date = datetime.now()


    query = db.session.query(
        User,
        func.count(BorrowSlip.id).label('borrow_count')
    ).join(BorrowSlip, User.id == BorrowSlip.reader_id) \
     .filter(BorrowSlip.status.in_([BorrowStatus.RETURNED, BorrowStatus.BORROWING, BorrowStatus.OVERDUE]))


    # Filter by reference month/year
    query = query.filter(
        db.extract('month', BorrowSlip.created_at) == ref_date.month,
        db.extract('year', BorrowSlip.created_at) == ref_date.year
    )


    readers = query.group_by(User.id) \
     .order_by(func.count(BorrowSlip.id).desc()) \
     .limit(limit).all()


    return readers




def get_category_distribution():
    """Get book distribution by category for pie chart"""
    from sqlalchemy import func


    categories = db.session.query(
        Category,
        func.count(Book.id).label('book_count')
    ).join(CategoryBook, Category.id == CategoryBook.category_id) \
     .join(Book, CategoryBook.book_id == Book.id) \
     .group_by(Category.id) \
     .all()


    total = sum(c.book_count for c in categories)
    result = []
    for cat, count in categories:
        percentage = (count / total * 100) if total > 0 else 0
        result.append({
            'name': cat.name,
            'count': count,
            'percentage': round(percentage, 1)
        })


    return sorted(result, key=lambda x: x['percentage'], reverse=True)




def get_borrow_status_breakdown():
    """Get breakdown of borrow slips by status"""
    stats = {}
    for status in BorrowStatus:
        count = BorrowSlip.query.filter(BorrowSlip.status == status).count()
        stats[status.value] = count
    return stats




def get_recent_activities(limit=10):
    """Get recent borrowing activities"""
    from library_digital.models import BorrowSlip


    activities = BorrowSlip.query \
        .order_by(BorrowSlip.updated_at.desc()) \
        .limit(limit).all()


    return activities

def get_viewed_books(reader_id):
    views = (
        ViewHistory.query
        .options(joinedload(ViewHistory.book))  # tránh N+1 query
        .filter_by(reader_id=reader_id)
        .order_by(ViewHistory.count.desc())
        .limit(5)
        .all()
    )

    return [
        {
            "id": v.book.id,
            "title": v.book.title
        }
        for v in views if v.book
    ]

def get_borrowed_books(reader_id):
    slips = (
        BorrowSlip.query
        .options(joinedload(BorrowSlip.book))  # tránh N+1 query
        .filter(
            BorrowSlip.reader_id == reader_id,
            BorrowSlip.status.in_(["BORROWING", "RETURNED"])
        )
        .all()
    )

    return [
        {
            "id": s.book.id,
            "title": s.book.title
        }
        for s in slips if s.book
    ]

def get_favorite_categories(reader_id):
    categories = (
        ReaderCategory.query
        .options(joinedload(ReaderCategory.category))  # tránh N+1
        .filter_by(user_id=reader_id)
        .all()
    )

    return [
        {
            "id": c.category.id,
            "name": c.category.name
        }
        for c in categories if c.category_id
    ]

def get_candidate_books(reader_id):
    books = (
        db.session.query(Book)
        .join(CategoryBook, Book.id == CategoryBook.book_id)
        .join(ReaderCategory, CategoryBook.category_id == ReaderCategory.category_id)
        .filter(
            ReaderCategory.user_id == reader_id,
            Book.is_active == True
        )
        .distinct()
        .limit(20)
        .all()
    )

    return [
        {
            "id": b.id,
            "title": b.title
        }
        for b in books
    ]

def build_profile(reader_id):
    return {
        "views": get_viewed_books(reader_id),
        "borrows": get_borrowed_books(reader_id),
        "categories": get_favorite_categories(reader_id)
    }

def parse_ai_response(ai_text):
    try:
        return json.loads(ai_text)
    except:
        return []


def map_to_books(ai_result, candidates):
    book_map = {b["title"]: b["id"] for b in candidates}

    final = []

    for item in ai_result:
        title = item["title"]
        if title in book_map:
            final.append({
                "id": book_map[title],
                "title": title,
                "reason": item["reason"]
            })

    return final

def recommend_books(reader_id):

    profile = build_profile(reader_id)
    candidates = get_candidate_books(reader_id)  # [{id, title}]

    ai_text = call_ai(profile, candidates)

    ai_json = parse_ai_response(ai_text)

    final = map_to_books(ai_json, candidates)

    if not candidates:
        return []

    return final
