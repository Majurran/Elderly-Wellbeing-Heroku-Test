from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import os 

db = SQLAlchemy()
DB_NAME = "database_ver12.db"  # Change name if the models.py gets updated for now

from flask_socketio import SocketIO
socketio = SocketIO()

def create_app(debug=False):
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    
    UPLOAD_FOLDER = os.path.join(app.static_folder, "input_option_img")
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1000 * 1000   # 2 MB max image limit
    
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    socketio.init_app(app)
    return app

def create_database(app):
    if not path.exists(os.path.join("website", DB_NAME)):
        db.create_all(app=app)
        print('Created Database!')
