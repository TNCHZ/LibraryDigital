from flask import Flask, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from future.backports.datetime import datetime

from library_digital import create_app, login, utils
import cloudinary.uploader
from library_digital.extensions import db

app = create_app()

@app.route('/')
def home():
    cates = utils.get_categories()
    return render_template('user/home.html', cates=cates)

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
    return render_template('user/borrow_history.html')

@app.route('/user/<int:user_id>/borrow-status')
def borrow_status(user_id):
    return render_template('user/borrow_status.html')

@app.route('/book/searching_book/')
def book_searching():
    return render_template('user/searching_book.html')

@app.route('/librarian/book_management/')
def librarian_book_management():
    return render_template('librarian/book_management.html')


@app.route('/librarian/dashboard/')
def librarian_dashboard():
    return render_template('librarian/dashboard.html')


@app.route('/librarian/reader_management/')
def librarian_reader_management():
    return render_template('librarian/reader_management.html')


@app.route('/librarian/borrow_slip_management/')
def librarian_borrow_slip_management():
    return render_template('librarian/borrow_slip_management.html')


@app.route('/admin/borrow_slip_management/')
def admin_borrow_slip_management():
    return render_template('admin/borrow_slip_management.html')

@app.route('/admin/user_management/')
def admin_user_management():
    return render_template('admin/user_management.html')


@app.route('/admin/dashboard/')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/book_management/')
def admin_book_management():
    return render_template('admin/book_management.html')

@app.route('/admin/report/')
def admin_report():
    return render_template('admin/report.html')


@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    reader_id = current_user.id

    can, message = utils.can_borrow(reader_id, book_id)
    book = utils.get_book_by_id(book_id)

    if not can:
        return render_template(
            "/user/book_detail.html",
            book = book,
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

if __name__ == "__main__":
    app.run(debug=True) 