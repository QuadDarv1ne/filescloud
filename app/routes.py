"""
Модуль routes.py - основной маршрутизатор приложения FilesCloud.

Содержит обработчики для:
- Главной страницы с файлами
- Загрузки/скачивания/удаления файлов
- Регистрации/авторизации пользователей
- Обработки ошибок
"""

"""
Модуль routes.py - основной маршрутизатор приложения FilesCloud.
"""

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, send_from_directory, current_app, abort
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import logging
from datetime import datetime, timedelta
from urllib.parse import quote

from app import db
from app.forms import RegistrationForm, LoginForm, ShareSettingsForm
from app.models import User, File, ShareLink
from app.utils import (
    allowed_file,
    generate_secure_filename,
    validate_file_ownership,
    handle_database_error
)

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main.route('/')
@login_required
def index():
    """Главная страница с файлами пользователя"""
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('q', '').strip()
        per_page = current_app.config['ITEMS_PER_PAGE']

        query = File.query.filter(
            File.user_id == current_user.id,
            File.is_deleted == False
        )

        if search_query:
            search = f"%{search_query}%"
            query = query.filter(File.filename.ilike(search))

        files = query.order_by(File.uploaded_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return render_template('main/index.html', files=files)

    except Exception as e:
        return handle_database_error(e)

@main.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Обработка загрузки файлов"""
    try:
        if request.content_length > current_app.config['MAX_CONTENT_LENGTH']:
            abort(413)

        if 'file' not in request.files:
            flash('Файл не выбран', 'danger')
            return redirect(url_for('main.index'))

        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            flash('Недопустимый файл', 'danger')
            return redirect(url_for('main.index'))

        filename = generate_secure_filename(file.filename)
        user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, filename)

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

    except RequestEntityTooLarge:
        abort(413)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        flash('Ошибка при загрузке файла', 'danger')

    return redirect(url_for('main.index'))

@main.route('/download/<filename>')
@login_required
def download_file(filename):
    """Скачивание файла"""
    try:
        user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        return send_from_directory(
            user_dir,
            filename,
            as_attachment=True,
            download_name=secure_filename(filename)
        )
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}")
        abort(404)

@main.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """Мягкое удаление файла"""
    try:
        file = File.query.filter_by(
            id=file_id,
            user_id=current_user.id,
            is_deleted=False
        ).first_or_404()

        file.is_deleted = True
        file.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Файл перемещен в корзину', 'success')
        logger.info(f"User {current_user.id} deleted {file.filename}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        flash('Ошибка при удалении файла', 'danger')

    return redirect(url_for('main.index'))

@main.route('/restore/<int:file_id>', methods=['POST'])
@login_required
def restore_file(file_id):
    """Восстановление файла из корзины"""
    try:
        file = File.query.filter_by(
            id=file_id,
            user_id=current_user.id,
            is_deleted=True
        ).first_or_404()

        file.is_deleted = False
        file.deleted_at = None
        db.session.commit()
        flash('Файл успешно восстановлен', 'success')
        logger.info(f"User {current_user.id} restored {file.filename}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Restore error: {str(e)}", exc_info=True)
        flash('Ошибка при восстановлении файла', 'danger')

    return redirect(url_for('main.trash'))

@main.route('/purge/<int:file_id>', methods=['POST'])
@login_required
def purge_file(file_id):
    """Полное удаление файла"""
    try:
        file = File.query.filter_by(
            id=file_id,
            user_id=current_user.id,
            is_deleted=True
        ).first_or_404()

        os.remove(file.storage_path)
        db.session.delete(file)
        db.session.commit()
        flash('Файл удален навсегда', 'success')
        logger.info(f"User {current_user.id} purged {file.filename}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Purge error: {str(e)}", exc_info=True)
        flash('Ошибка при удалении файла', 'danger')

    return redirect(url_for('main.trash'))

@main.route('/trash')
@login_required
def trash():
    """Страница корзины"""
    try:
        files = File.query.filter_by(
            user_id=current_user.id,
            is_deleted=True
        ).order_by(File.deleted_at.desc()).all()

        return render_template('main/trash.html', files=files)

    except Exception as e:
        return handle_database_error(e)

@main.route('/share/<int:file_id>', methods=['GET', 'POST'])
@login_required
def share_file(file_id):
    """Управление общим доступом к файлу"""
    try:
        file = validate_file_ownership(file_id)
        form = ShareSettingsForm()

        if form.validate_on_submit():
            # Создание или обновление ссылки
            share_link = ShareLink.query.filter_by(file_id=file.id).first()

            if not share_link:
                share_link = ShareLink(file_id=file.id)
                db.session.add(share_link)

            share_link.expiration = datetime.utcnow() + timedelta(
                seconds=form.expiration.data
            ) if form.expiration.data else None
            share_link.password = form.password.data
            share_link.download_limit = form.download_limit.data
            share_link.token = os.urandom(16).hex()

            db.session.commit()
            flash('Настройки доступа обновлены', 'success')
            return redirect(url_for('main.share_file', file_id=file.id))

        share_link = ShareLink.query.filter_by(file_id=file.id).first()
        share_url = url_for(
            'main.shared_download',
            token=share_link.token if share_link else '',
            _external=True
        ) if share_link else ''

        return render_template(
            'main/share.html',
            file=file,
            form=form,
            share_url=share_url,
            expiration=share_link.expiration if share_link else None
        )

    except Exception as e:
        return handle_database_error(e)

@main.route('/shared/<token>', methods=['GET', 'POST'])
def shared_download(token):
    """Скачивание по общей ссылке"""
    try:
        share_link = ShareLink.query.filter_by(token=token).first_or_404()
        file = File.query.get_or_404(share_link.file_id)

        # Проверка срока действия
        if share_link.expiration and share_link.expiration < datetime.utcnow():
            flash('Срок действия ссылки истек', 'danger')
            abort(410)

        # Проверка пароля
        if share_link.password:
            if request.method == 'POST':
                if request.form.get('password') != share_link.password:
                    flash('Неверный пароль', 'danger')
            else:
                return render_template('shared_password.html')

        # Проверка лимита скачиваний
        if share_link.download_limit and share_link.download_count >= share_link.download_limit:
            flash('Лимит скачиваний исчерпан', 'danger')
            abort(410)

        share_link.download_count += 1
        db.session.commit()

        return send_from_directory(
            os.path.dirname(file.storage_path),
            os.path.basename(file.storage_path),
            as_attachment=True,
            download_name=quote(file.filename)
        )

    except Exception as e:
        logger.error(f"Shared download error: {str(e)}", exc_info=True)
        abort(404)

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
    
    return render_template('auth/register.html', form=form)


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
    
    return render_template('auth/login.html', form=form)


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

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )
