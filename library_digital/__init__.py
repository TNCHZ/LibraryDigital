from flask import Flask
from .extensions import db
import cloudinary
from flask_login import LoginManager

login = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'abc123'

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Admin%40123@localhost/librarydb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login.init_app(app)

    return app


cloudinary.config(
    cloud_name = 'dq1oo3fod',
    api_key = '216276187471198',
    api_secret = 'IPwc-sSRfgqIY30pkisZ_SBINC8'
)

