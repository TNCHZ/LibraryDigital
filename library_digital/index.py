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

@app.route('/user/<int:user_id>')
def user_detail(user_id):
    return render_template('user/user_detail.html', user_id=user_id)

@app.route('/user/<int:user_id>/borrow-history')
def borrow_history(user_id):
    return render_template('user/borrow_history.html')

@app.route('/user/<int:user_id>/borrow-status')
def borrow_status(user_id):
    return render_template('user/borrow_status.html')

if __name__ == "__main__":
    app.run(debug=True) 