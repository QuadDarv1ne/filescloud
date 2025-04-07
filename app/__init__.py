from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel, lazy_gettext
import logging

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filescloud.db'
    app.config['UPLOAD_FOLDER'] = 'uploads/'
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'docx', 'xlsx'}
    app.config['BABEL_DEFAULT_LOCALE'] = 'ru'

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)

    # @babel.localeselector
    # def get_locale():
    #     return request.accept_languages.best_match(['ru', 'en'])

    if not app.debug:
        logging.basicConfig(level=logging.INFO)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
