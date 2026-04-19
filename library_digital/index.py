from flask import Flask, render_template
from flask_login import login_user, logout_user, current_user, login_required

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('user/home.html')

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    return render_template('user/book_detail.html', book_id=book_id)

@app.route('/auth/login')
def login():
    return render_template('auth/login.html')

@app.route('/auth/register')
def register():
    return render_template('auth/register.html')

@app.route('/auth/forget-password')
def forget_pass():
    return render_template('auth/forget_password.html')

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

if __name__ == "__main__":
    app.run(debug=True) 