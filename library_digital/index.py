from library_digital import app
from flask_login import login_user, logout_user, current_user, login_required



if __name__ == "__main__":
    app.run(debug=True)