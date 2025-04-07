from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, File
from .forms import RegistrationForm, LoginForm
import os
from datetime import datetime

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main.route('/')
@login_required
def index():
    query = request.args.get('q')
    if query:
        files = File.query.filter(File.filename.contains(query), File.user_id == current_user.id).all()
    else:
        files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', files=files)

@main.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('Нет файла для загрузки', 'danger')
        return redirect(url_for('main.index'))
    file = request.files['file']
    if file.filename == '':
        flash('Файл не выбран', 'danger')
        return redirect(url_for('main.index'))
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        new_file = File(filename=filename, user_id=current_user.id, upload_date=datetime.utcnow())
        db.session.add(new_file)
        db.session.commit()
        flash('Файл успешно загружен', 'success')
        return redirect(url_for('main.index'))
    else:
        flash('Недопустимый тип файла', 'danger')
        return redirect(url_for('main.index'))

@main.route('/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@main.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash('У вас нет прав на удаление этого файла', 'danger')
        return redirect(url_for('main.index'))
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(file)
    db.session.commit()
    flash('Файл успешно удален', 'success')
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Ваш аккаунт был создан! Теперь вы можете войти', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))
