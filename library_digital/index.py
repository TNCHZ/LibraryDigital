from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from future.backports.datetime import datetime
from datetime import datetime

from library_digital import create_app, login, utils
import cloudinary.uploader
from library_digital.extensions import db

app = create_app()

@app.route('/')
def home():
    cates = utils.get_categories()
    reader_id = current_user.id
    notes = utils.recommend_books(reader_id)
    result = []

    for item in notes:
        book = utils.get_book_by_id(item['id'])

        if book:
            result.append({
                "book": book,
                "reason": item["reason"]
            })


    return render_template('user/home.html', cates=cates, result = result)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = utils.get_book_by_id(book_id)

    return render_template('user/book_detail.html', book=book)

@app.route('/auth/login', methods=['get', 'post'])
def user_login():
    err_msg = ''

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = utils.check_login(username=username, password=password, role=role)
        if user:
            login_user(user=user)
            if user.role.value =="ADMIN":
                return redirect(url_for('admin_dashboard'))
            elif user.role.value =="LIBRARIAN":
                return redirect(url_for('librarian_dashboard'))
            else:
                return redirect(url_for('home'))
            return redirect(url_for('home'))
        else:
            err_msg = "Sai tài khoản hoặc mật khẩu!!!"

    return render_template('auth/login.html', err_msg=err_msg)

@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)

@app.route('/auth/logout')
def user_logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/auth/register', methods=['get', 'post'])
def register():
    err_msg = ""

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        email = request.form.get('email')
        gender = request.form.get('gender')
        confirm = request.form.get('confirm_password')
        avatar_path = None

        try:
            if password.strip() == confirm.strip():
                avatar = request.files.get('avatar')
                if avatar:
                    res = cloudinary.uploader.upload(avatar)
                    avatar_path = res['secure_url']
                utils.add_user(first_name=first_name, last_name=last_name, username=username, password=password, email=email, phone=phone, gender=gender, avatar=avatar_path)
                return redirect(url_for('user_login'))
            else:
                err_msg = "Mật khẩu không khớp!!!"
        except Exception as ex:
            err_msg = 'Hệ thống đang gặp lỗi: ' + str(ex)

    return render_template('auth/register.html', err_msg=err_msg)

@app.route('/update-avatar', methods=['POST'])
@login_required
def update_avatar():
    avatar = request.files.get('avatar')

    if not avatar or avatar.filename == "":
        flash("Vui lòng chọn ảnh!", "error")
        return redirect(url_for('user_detail', user_id=current_user.id))

    try:
        res = cloudinary.uploader.upload(avatar)
        current_user.avatar = res.get("secure_url")

        db.session.commit()
        flash("Cập nhật avatar thành công!", "success")

    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Upload thất bại!", "error")

    return redirect(url_for('user_detail', user_id=current_user.id))

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    success, message = utils.update_user_profile(
        user=current_user,
        first_name=request.form.get('first_name'),
        last_name=request.form.get('last_name'),
        email=request.form.get('email'),
        phone=request.form.get('phone'),
        gender=request.form.get('gender'))

    flash(message, "success" if success else "error")

    return redirect(url_for('user_detail', user_id=current_user.id))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    success, message = utils.change_user_password(
        user=current_user,
        current_password=request.form.get('current_password'),
        new_password=request.form.get('new_password'),
        confirm_password=request.form.get('confirm_password')
    )

    flash(message, "success" if success else "error")

    return redirect(url_for('user_detail', user_id=current_user.id))

@app.route('/auth/forget-password')
def forget_pass():
    return render_template('auth/forget_password.html')

@app.route('/categories')
def category_list():
    cates = utils.get_categories()
    category_id = request.args.get('category_id')

    if category_id:
        books = utils.get_books_by_category(category_id)
    else:
        books = utils.get_books()

    return render_template('user/categories.html', cates=cates, current_category_id=category_id, books=books)

@app.route('/user/<int:user_id>/profile')
def user_detail(user_id):
    return render_template('user/user_detail.html', user_id=user_id)

@app.route('/user/<int:user_id>/borrow-history')
def borrow_history(user_id):
    reader_id = request.args.get("reader_id", user_id, type=int)
    page = request.args.get("page", 1, type=int)

    data = utils.get_borrow_slips_by_reader(reader_id, page)
    return render_template('user/borrow_history.html', data=data, user_id=user_id)

@app.route('/user/<int:user_id>/borrow-status')
def borrow_status(user_id):
    slip = utils.get_reserved_slip_by_reader(user_id)

    return render_template('user/borrow_status.html', slip=slip)

@app.route('/book/searching-book/', methods=['GET'])
def book_searching():
    isbn_10 = request.args.get('isbn_10', '').strip()
    isbn_13 = request.args.get('isbn_13', '').strip()
    title = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    category_ids = request.args.getlist('category_ids', type=int)
    page = request.args.get('page', 1, type=int)

    categories = utils.get_categories()

    if title or author or category_ids or isbn_10 or isbn_13:
        pagination = utils.search_books(isbn_10=isbn_10 or None, isbn_13=isbn_13 or None, title=title or None, author=author or None, category_ids=category_ids or None, page=page, per_page=8)
    else:
        pagination = utils.search_books(page=page, per_page=8)

    return render_template('user/searching_book.html',
                           books=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           search_title=title,
                           search_author=author,
                           selected_category_ids=category_ids,
                           search_isbn_10=isbn_10,
                           search_isbn_13=isbn_13)

@app.route('/librarian/book-management/', methods=['GET'])
def librarian_book_management():
    isbn_10 = request.args.get('isbn_10', '').strip()
    isbn_13 = request.args.get('isbn_13', '').strip()
    title = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    category_ids = request.args.getlist('category_ids', type=int)
    page = request.args.get('page', 1, type=int)

    categories = utils.get_categories()
    pagination = utils.search_books(isbn_10=isbn_10 or None, isbn_13=isbn_13 or None, title=title or None, author=author or None, category_ids=category_ids or None, page=page, per_page=10)

    return render_template('librarian/book_management.html',
                           books=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           search_title=title,
                           search_author=author,
                           selected_category_ids=category_ids,
                           search_isbn_10=isbn_10,
                           search_isbn_13=isbn_13)

@app.route('/librarian/dashboard/')
def librarian_dashboard():
    return render_template('librarian/dashboard.html')

@app.route('/librarian/reader_management/')
def librarian_reader_management():
    return render_template('librarian/reader_management.html')


@app.route('/librarian/borrow-slip-management/')
@login_required
def librarian_borrow_slip_management():
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    borrow_slips = utils.get_borrow_slips(status=status if status else None, page=page, per_page=10)

    return render_template(
        'librarian/borrow_slip_management.html',
        borrow_slips=borrow_slips,
        status_filter=status,
        BorrowStatus=utils.BorrowStatus
    )


@app.route('/librarian/borrow-slip/<int:slip_id>/approve/', methods=['POST'])
@login_required
def librarian_approve_borrow_slip(slip_id):
    success, message = utils.approve_borrow_slip(slip_id, current_user.id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('librarian_borrow_slip_management'))


@app.route('/librarian/borrow-slip/<int:slip_id>/reject/', methods=['POST'])
@login_required
def librarian_reject_borrow_slip(slip_id):
    note = request.form.get('reject_note', '').strip()
    success, message = utils.reject_borrow_slip(slip_id, current_user.id, note)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('librarian_borrow_slip_management'))


@app.route('/admin/borrow-slip-management/')
@login_required
def admin_borrow_slip_management():
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    borrow_slips = utils.get_borrow_slips(status=status if status else None, page=page, per_page=10)

    return render_template(
        'admin/borrow_slip_management.html',
        borrow_slips=borrow_slips,
        status_filter=status,
        BorrowStatus=utils.BorrowStatus
    )


@app.route('/admin/borrow-slip/<int:slip_id>/approve/', methods=['POST'])
@login_required
def admin_approve_borrow_slip(slip_id):
    success, message = utils.approve_borrow_slip(slip_id, current_user.id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_borrow_slip_management'))


@app.route('/admin/borrow-slip/<int:slip_id>/reject/', methods=['POST'])
@login_required
def admin_reject_borrow_slip(slip_id):
    note = request.form.get('reject_note', '').strip()
    success, message = utils.reject_borrow_slip(slip_id, current_user.id, note)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_borrow_slip_management'))


@app.route('/admin/user_management/')
def admin_user_management():
    role = request.args.get('role')  # ADMIN / LIBRARIAN / READER
    status = request.args.get('status')  # active / inactive

    is_active = None
    if status == "active":
        is_active = True
    elif status == "inactive":
        is_active = False

    users = utils.get_users(role=role, is_active=is_active)
    stats = utils.get_user_stats()

    return render_template(
        'admin/user_management.html',
        users=users,
        **stats
    )


@app.route('/admin/dashboard/')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/book-management/', methods=['GET'])
def admin_book_management():
    isbn_10 = request.args.get('isbn_10', '').strip()
    isbn_13 = request.args.get('isbn_13', '').strip()
    title = request.args.get('title', '').strip()
    author = request.args.get('author', '').strip()
    category_ids = request.args.getlist('category_ids', type=int)
    page = request.args.get('page', 1, type=int)

    categories = utils.get_categories()
    pagination = utils.search_books(isbn_10=isbn_10 or None, isbn_13=isbn_13 or None, title=title or None, author=author or None, category_ids=category_ids or None, page=page, per_page=10)

    return render_template('admin/book_management.html',
                           books=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           search_title=title,
                           search_author=author,
                           selected_category_ids=category_ids,
                           search_isbn_10=isbn_10,
                           search_isbn_13=isbn_13)

@app.route('/admin/report/')
def admin_report():
    return render_template('admin/report.html')


# ==================== LIBRARIAN BOOK CRUD ====================
@app.route('/librarian/book/add/', methods=['POST'])
def librarian_add_book():
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        publisher = request.form.get('publisher', '').strip()
        published_date = request.form.get('published_date', type=int)
        price = request.form.get('price', type=float)
        author = request.form.get('author', '').strip()
        isbn_10 = request.form.get('isbn_10', '').strip()
        isbn_13 = request.form.get('isbn_13', '').strip()
        language = request.form.get('language', '').strip()
        category_ids = request.form.getlist('category_ids', type=int)

        # Handle image upload
        image = request.files.get('image')
        image_url = ''
        if image:
            res = cloudinary.uploader.upload(image)
            image_url = res['secure_url']
        else:
            image_url = 'https://via.placeholder.com/300x400?text=No+Cover'

        librarian_id = current_user.id if current_user.is_authenticated else None

        utils.add_book(
            title=title, description=description, publisher=publisher,
            published_date=published_date, price=price, author=author,
            isbn_10=isbn_10, isbn_13=isbn_13, image=image_url,
            language=language, category_ids=category_ids,
            librarian_id=librarian_id
        )

        return redirect(url_for('librarian_book_management'))
    except Exception as ex:
        return str(ex), 500


@app.route('/librarian/book/edit/<int:book_id>/', methods=['POST'])
def librarian_edit_book(book_id):
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        publisher = request.form.get('publisher', '').strip()
        published_date = request.form.get('published_date', type=int)
        price = request.form.get('price', type=float)
        author = request.form.get('author', '').strip()
        isbn_10 = request.form.get('isbn_10', '').strip()
        isbn_13 = request.form.get('isbn_13', '').strip()
        language = request.form.get('language', '').strip()
        is_active = request.form.get('is_active') == 'on'
        category_ids = request.form.getlist('category_ids', type=int)

        # Handle image upload
        image = request.files.get('image')
        image_url = None
        if image:
            res = cloudinary.uploader.upload(image)
            image_url = res['secure_url']

        utils.update_book(
            book_id=book_id, title=title, description=description,
            publisher=publisher, published_date=published_date, price=price,
            author=author, isbn_10=isbn_10, isbn_13=isbn_13, image=image_url,
            language=language, is_active=is_active, category_ids=category_ids
        )

        return redirect(url_for('librarian_book_management'))
    except Exception as ex:
        return str(ex), 500


@app.route('/librarian/book/delete/<int:book_id>/', methods=['POST'])
def librarian_delete_book(book_id):
    try:
        success = utils.delete_book(book_id)
        if success:
            return redirect(url_for('librarian_book_management'))
        else:
            return "Book not found", 404
    except Exception as ex:
        return str(ex), 500


# ==================== ADMIN BOOK CRUD ====================
@app.route('/admin/book/add/', methods=['POST'])
def admin_add_book():
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        publisher = request.form.get('publisher', '').strip()
        published_date = request.form.get('published_date', type=int)
        price = request.form.get('price', type=float)
        author = request.form.get('author', '').strip()
        isbn_10 = request.form.get('isbn_10', '').strip()
        isbn_13 = request.form.get('isbn_13', '').strip()
        language = request.form.get('language', '').strip()
        category_ids = request.form.getlist('category_ids', type=int)

        # Handle image upload
        image = request.files.get('image')
        image_url = ''
        if image:
            res = cloudinary.uploader.upload(image)
            image_url = res['secure_url']
        else:
            image_url = 'https://via.placeholder.com/300x400?text=No+Cover'

        utils.add_book(
            title=title, description=description, publisher=publisher,
            published_date=published_date, price=price, author=author,
            isbn_10=isbn_10, isbn_13=isbn_13, image=image_url,
            language=language, category_ids=category_ids
        )

        return redirect(url_for('admin_book_management'))
    except Exception as ex:
        return str(ex), 500


@app.route('/admin/book/edit/<int:book_id>/', methods=['POST'])
def admin_edit_book(book_id):
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        publisher = request.form.get('publisher', '').strip()
        published_date = request.form.get('published_date', type=int)
        price = request.form.get('price', type=float)
        author = request.form.get('author', '').strip()
        isbn_10 = request.form.get('isbn_10', '').strip()
        isbn_13 = request.form.get('isbn_13', '').strip()
        language = request.form.get('language', '').strip()
        is_active = request.form.get('is_active') == 'on'
        category_ids = request.form.getlist('category_ids', type=int)

        # Handle image upload
        image = request.files.get('image')
        image_url = None
        if image:
            res = cloudinary.uploader.upload(image)
            image_url = res['secure_url']

        utils.update_book(
            book_id=book_id, title=title, description=description,
            publisher=publisher, published_date=published_date, price=price,
            author=author, isbn_10=isbn_10, isbn_13=isbn_13, image=image_url,
            language=language, is_active=is_active, category_ids=category_ids
        )

        return redirect(url_for('admin_book_management'))
    except Exception as ex:
        return str(ex), 500


@app.route('/admin/book/delete/<int:book_id>/', methods=['POST'])
def admin_delete_book(book_id):
    try:
        success = utils.delete_book(book_id)
        if success:
            return redirect(url_for('admin_book_management'))
        else:
            return "Book not found", 404
    except Exception as ex:
        return str(ex), 500

@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    reader_id = current_user.id

    can, message = utils.can_borrow(reader_id, book_id)

    book = utils.get_book_by_id(book_id)

    if not can:
        return render_template(
            "user/book_detail.html",
            book=book,
            msg=message
        )

    utils.add_borrow_slip(
        reader_id=reader_id,
        librarian_id=None,
        book_id=book_id,
        borrow_date=datetime.now(),
        due_date=None,
        return_date=None,
        status="RESERVED",
        note=""
    )

    return render_template(
        "user/book_detail.html",
        book=book,
        msg="Mượn sách thành công"
    )

@app.route('/admin/user/add/', methods=['POST'])
def admin_add_user():
    try:
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        gender = request.form.get('gender')  # MALE / FEMALE / OTHER
        role = request.form.get('role')      # ADMIN / LIBRARIAN / READER

        avatar = request.files.get('avatar')
        avatar_url = None

        if avatar:
            res = cloudinary.uploader.upload(avatar)
            avatar_url = res['secure_url']

        utils.admin_add_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            email=email,
            phone=phone,
            gender=gender,
            role=role,
            avatar=avatar_url
        )

        return redirect(url_for('admin_user_management'))

    except Exception as ex:
        return str(ex), 500

@app.route('/admin/user/edit/<int:user_id>/', methods=['POST'])
def admin_edit_user(user_id):
    try:
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        gender = request.form.get('gender')
        role = request.form.get('role')
        password = request.form.get('password')
        is_active = request.form.get('is_active') == 'on'

        # upload avatar
        avatar = request.files.get('avatar')
        avatar_url = None
        if avatar:
            res = cloudinary.uploader.upload(avatar)
            avatar_url = res['secure_url']

        utils.update_user(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            phone=phone,
            gender=gender,
            role=role,
            password=password,
            is_active=is_active,
            avatar=avatar_url
        )

        return redirect(url_for('admin_user_management'))

    except Exception as ex:
        return str(ex), 500

@app.route('/admin/user/delete/<int:user_id>/', methods=['POST'])
def admin_delete_user(user_id):
    try:
        utils.delete_user(user_id)
        return redirect(url_for('admin_user_management'))
    except Exception as ex:
        return str(ex), 500

@app.route('/admin/statistics/')
@login_required
def admin_statistics():
    from library_digital import utils
    from datetime import datetime, timedelta

    # Get period from query params
    period = request.args.get('period', 'current')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Calculate reference date based on period
    now = datetime.now()
    if period == 'last':
        # Last month
        if now.month == 1:
            ref_date = datetime(now.year - 1, 12, 1)
        else:
            ref_date = datetime(now.year, now.month - 1, 1)
    elif period == 'custom' and start_date and end_date:
        # Custom date range - use end_date as reference
        ref_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        # Current month (default)
        ref_date = now
        period = 'current'

    # Get comprehensive statistics with reference date
    stats = utils.get_dashboard_statistics(ref_date=ref_date)
    monthly_stats = utils.get_monthly_loan_stats(ref_date=ref_date)
    top_readers = utils.get_top_readers(5, ref_date=ref_date)
    category_dist = utils.get_category_distribution()
    status_breakdown = utils.get_borrow_status_breakdown()
    recent_activities = utils.get_recent_activities(10)

    return render_template('admin/statistics.html',
                         stats=stats,
                         monthly_stats=monthly_stats,
                         top_readers=top_readers,
                         category_dist=category_dist,
                         status_breakdown=status_breakdown,
                         recent_activities=recent_activities,
                         current_period=period,
                         start_date=start_date,
                         end_date=end_date)
    
    
if __name__ == "__main__":
    app.run(debug=True)
