import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

from app import db  # Добавить в начало файла

def allowed_file(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_secure_filename(filename):
    return f"{uuid.uuid4().hex}_{secure_filename(filename)}"

def validate_file_ownership(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        abort(403)
    return file

def handle_database_error(error):
    current_app.logger.error(f"Database error: {str(error)}")
    db.session.rollback()
    flash('A database error occurred', 'danger')
    return redirect(url_for('main.index'))
