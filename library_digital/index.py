from flask import Flask, render_template
from flask_login import login_user, logout_user, current_user, login_required

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('user/home.html')

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    return render_template('user/book_detail.html', book_id=book_id)


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




if __name__ == "__main__":
    app.run(debug=True) 