from datetime import datetime
import os
import logging
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, locale_selector=get_locale)
    csrf.init_app(app)

    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'danger'
    login_manager.login_message = 'Please log in to access this page.'

    upload_path = Path(app.config['UPLOAD_FOLDER'])
    upload_path.mkdir(exist_ok=True, parents=True)

    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler()
            ]
        )

    # Добавление фильтров
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d.%m.%Y %H:%M'):
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('filesizeformat')
    def filesizeformat(value):
        # Улучшенный форматировщик размеров файлов
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs(value) < 1024.0:
                return f"{value:3.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} TB"
    
    @app.context_processor
    def inject_now():
        # Добавляет текущий год в футер
        return {'now': datetime.utcnow()}
    
    return app

def get_locale():
    from flask import request, session
    return request.args.get('lang') or session.get('lang') or 'ru'

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))