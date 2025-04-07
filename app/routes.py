"""
Модуль routes.py - основной маршрутизатор приложения FilesCloud.

Содержит обработчики для:
- Главной страницы с файлами
- Загрузки/скачивания/удаления файлов
- Регистрации/авторизации пользователей
- Обработки ошибок
"""

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, send_from_directory, current_app, abort
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime

from app import db
from app.forms import RegistrationForm, LoginForm
from app.models import User, File
from app.utils import allowed_file, generate_secure_filename

# Инициализация Blueprint
main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


def handle_database_error(e: Exception, redirect_url: str = 'main.index') -> redirect:
    """
    Обрабатывает ошибки базы данных и перенаправляет пользователя.

    Args:
        e (Exception): Пойманное исключение
        redirect_url (str): URL для перенаправления

    Returns:
        redirect: Перенаправление на указанный URL
    """
    logger.error(f"Database error: {str(e)}", exc_info=True)
    db.session.rollback()
    flash('Произошла ошибка базы данных', 'danger')
    return redirect(url_for(redirect_url))


@main.route('/')
@login_required
def index() -> str:
    """
    Отображает главную страницу с файлами пользователя.

    Returns:
        str: HTML-страница с файлами
        redirect: Перенаправление при ошибке

    Raises:
        Exception: Любые ошибки при работе с базой данных
    """
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('q', '').strip()
        per_page = current_app.config['ITEMS_PER_PAGE']

        # Основной запрос файлов
        query = File.query.filter_by(
            user_id=current_user.id,
            is_deleted=False
        )

        # Применение поискового запроса
        if search_query:
            search = f"%{search_query}%"
            query = query.filter(File.filename.ilike(search))

        # Пагинация результатов
        files = query.order_by(File.uploaded_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return render_template('index.html', files=files)

    except Exception as e:
        return handle_database_error(e)


@main.route('/upload', methods=['POST'])
@login_required
def upload_file() -> redirect:
    """
    Обрабатывает загрузку файлов на сервер.

    Returns:
        redirect: Перенаправление на главную страницу

    Raises:
        Exception: Ошибки при сохранении файла или работе с БД
    """
    if 'file' not in request.files:
        flash('Файл не выбран', 'danger')
        return redirect(url_for('main.index'))

    file = request.files['file']
    
    # Валидация входных данных
    if file.filename == '':
        flash('Файл не выбран', 'danger')
        return redirect(url_for('main.index'))

    if not allowed_file(file.filename):
        flash('Недопустимый тип файла', 'danger')
        return redirect(url_for('main.index'))

    try:
        # Генерация уникального имени файла
        filename = generate_secure_filename(file.filename)
        user_dir = os.path.join(
            current_app.config['UPLOAD_FOLDER'], 
            str(current_user.id)
        )
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, filename)

        # Сохранение файла и записи в БД
        file.save(file_path)
        new_file = File(
            filename=filename,
            storage_path=file_path,
            size=os.path.getsize(file_path),
            user_id=current_user.id
        )

        db.session.add(new_file)
        db.session.commit()
        flash('Файл успешно загружен', 'success')
        logger.info(f"User {current_user.id} uploaded {filename}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        flash('Ошибка при загрузке файла', 'danger')
    finally:
        db.session.close()

    return redirect(url_for('main.index'))


@main.route('/download/<filename>')
@login_required
def download_file(filename: str) -> send_from_directory:
    """
    Обеспечивает скачивание файла.

    Args:
        filename (str): Имя файла для скачивания

    Returns:
        send_from_directory: Файл для скачивания
        abort: 404 если файл не найден
    """
    try:
        user_upload_dir = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            str(current_user.id)
        )
        return send_from_directory(
            user_upload_dir,
            filename,
            as_attachment=True,
            download_name=secure_filename(filename)
        )
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}")
        abort(404)


@main.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id: int) -> redirect:
    """
    Помечает файл как удаленный (мягкое удаление).

    Args:
        file_id (int): ID файла для удаления

    Returns:
        redirect: Перенаправление на главную страницу
    """
    try:
        file = File.query.filter_by(
            id=file_id,
            user_id=current_user.id,
            is_deleted=False
        ).first_or_404()

        # Мягкое удаление файла
        file.is_deleted = True
        db.session.commit()
        flash('Файл перемещен в корзину', 'success')
        logger.info(f"User {current_user.id} deleted {file.filename}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        flash('Ошибка при удалении файла', 'danger')
    finally:
        db.session.close()

    return redirect(url_for('main.index'))


@main.route('/register', methods=['GET', 'POST'])
def register() -> str:
    """
    Обрабатывает регистрацию новых пользователей.

    Returns:
        str: HTML-форма регистрации
        redirect: Перенаправление после успешной регистрации
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Проверка уникальности имени пользователя
            existing_user = User.query.filter_by(
                username=form.username.data
            ).first()
            
            if existing_user:
                flash('Это имя пользователя уже занято', 'danger')
                return redirect(url_for('main.register'))

            # Создание нового пользователя
            hashed_password = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256'
            )
            
            user = User(
                username=form.username.data,
                password_hash=hashed_password
            )
            
            db.session.add(user)
            db.session.commit()
            flash('Аккаунт успешно создан! Можете войти', 'success')
            return redirect(url_for('main.login'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            flash('Ошибка при создании аккаунта', 'danger')
        finally:
            db.session.close()
    
    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login() -> str:
    """
    Обрабатывает авторизацию пользователей.

    Returns:
        str: HTML-форма авторизации
        redirect: Перенаправление после успешного входа
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(
                username=form.username.data
            ).first()
            
            if user and check_password_hash(user.password_hash, form.password.data):
                # Обновление времени последнего входа
                login_user(user)
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash('Вы успешно вошли в систему', 'success')
                return redirect(url_for('main.index'))
            
            flash('Неверные учетные данные', 'danger')

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            flash('Ошибка при входе в систему', 'danger')
    
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout() -> redirect:
    """
    Обрабатывает выход пользователя из системы.

    Returns:
        redirect: Перенаправление на страницу входа
    """
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('main.login'))


# Обработчики HTTP ошибок
@main.errorhandler(401)
def unauthorized_error(error) -> tuple:
    """
    Обрабатывает ошибку 401 - Неавторизованный доступ.
    
    Returns:
        tuple: (HTML-страница, HTTP статус)
    """
    return render_template('errors/401.html'), 401


@main.errorhandler(403)
def forbidden_error(error) -> tuple:
    """
    Обрабатывает ошибку 403 - Доступ запрещен.
    
    Returns:
        tuple: (HTML-страница, HTTP статус)
    """
    return render_template('errors/403.html'), 403


@main.errorhandler(404)
def page_not_found(error) -> tuple:
    """
    Обрабатывает ошибку 404 - Страница не найдена.
    
    Returns:
        tuple: (HTML-страница, HTTP статус)
    """
    return render_template('errors/404.html'), 404


@main.errorhandler(413)
def file_too_large(error) -> tuple:
    """
    Обрабатывает ошибку 413 - Слишком большой файл.
    
    Returns:
        tuple: (HTML-страница, HTTP статус)
    """
    return render_template('errors/413.html'), 413