"""
Модуль models.py - определяет структуру базы данных и бизнес-логику приложения.

Содержит модели:
- User: Модель пользователя системы
- File: Модель для хранения файловых метаданных
- ShareLink: Модель для управления общим доступом к файлам
"""

from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    """
    Модель пользователя системы.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя (первичный ключ)
        username (str): Уникальное имя пользователя (макс. 64 символа)
        password_hash (str): Хеш пароля пользователя (макс. 256 символов)
        created_at (datetime): Дата и время регистрации пользователя
        last_login (datetime): Дата и время последнего входа
        is_active (bool): Флаг активности аккаунта (по умолчанию True)
        files (relationship): Связь один-ко-многим с моделью File
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, doc="Уникальный идентификатор пользователя")
    username = db.Column(
        db.String(64), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="Уникальное имя пользователя (логин)")
    password_hash = db.Column(
        db.String(256), 
        nullable=False,
        doc="Хеш пароля пользователя (PBKDF2:sha256)")
    created_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow,
        doc="Дата и время создания аккаунта")
    last_login = db.Column(
        db.DateTime,
        doc="Дата и время последней успешной авторизации")
    is_active = db.Column(
        db.Boolean, 
        default=True,
        doc="Флаг активности аккаунта (True/False)")
    
    # Связи
    files = db.relationship(
        'File', 
        backref='owner', 
        lazy=True,
        cascade='all, delete-orphan',
        doc="Список файлов пользователя")

    def __repr__(self) -> str:
        """Строковое представление объекта пользователя"""
        return f'<User {self.username}>'


class File(db.Model):
    """
    Модель для хранения метаданных файлов.

    Атрибуты:
        id (int): Уникальный идентификатор файла (первичный ключ)
        filename (str): Оригинальное имя файла (макс. 256 символов)
        storage_path (str): Путь к файлу в файловой системе (макс. 512 символов)
        size (int): Размер файла в байтах
        user_id (int): Ссылка на владельца файла (внешний ключ)
        uploaded_at (datetime): Дата и время загрузки
        is_deleted (bool): Флаг мягкого удаления
        deleted_at (datetime): Дата и время удаления
    """
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True, doc="Уникальный идентификатор файла")
    filename = db.Column(
        db.String(256), 
        nullable=False,
        doc="Оригинальное имя файла")
    storage_path = db.Column(
        db.String(512), 
        nullable=False, 
        unique=True,
        doc="Физический путь к файлу")
    size = db.Column(
        db.BigInteger, 
        nullable=False,
        doc="Размер файла в байтах")
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True,
        doc="Внешний ключ к таблице пользователей")
    uploaded_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow,
        doc="Дата и время загрузки файла")
    is_deleted = db.Column(
        db.Boolean, 
        default=False, 
        index=True,
        doc="Флаг мягкого удаления файла")
    deleted_at = db.Column(
        db.DateTime,
        doc="Дата и время удаления файла")

    def __repr__(self) -> str:
        """Строковое представление объекта файла"""
        return f'<File {self.filename}>'


class ShareLink(db.Model):
    """
    Модель для управления общим доступом к файлам.

    Атрибуты:
        id (int): Уникальный идентификатор ссылки (первичный ключ)
        token (str): Уникальный токен доступа (32 символа)
        file_id (int): Ссылка на файл (внешний ключ)
        created_at (datetime): Дата и время создания ссылки
        expiration (datetime): Дата и время истечения срока действия
        password (str): Пароль для доступа (макс. 128 символов)
        download_limit (int): Максимальное количество скачиваний
        download_count (int): Текущее количество скачиваний
    """
    __tablename__ = 'share_links'
    
    id = db.Column(db.Integer, primary_key=True, doc="Уникальный идентификатор ссылки")
    token = db.Column(
        db.String(32), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="Уникальный токен доступа")
    file_id = db.Column(
        db.Integer, 
        db.ForeignKey('files.id', ondelete='CASCADE'), 
        nullable=False,
        doc="Внешний ключ к таблице файлов")
    created_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow,
        doc="Дата и время создания ссылки")
    expiration = db.Column(
        db.DateTime,
        doc="Дата и время истечения срока действия")
    password = db.Column(
        db.String(128),
        doc="Зашифрованный пароль для доступа")
    download_limit = db.Column(
        db.Integer, 
        default=0,
        doc="Лимит скачиваний (0 - без ограничений)")
    download_count = db.Column(
        db.Integer, 
        default=0,
        doc="Текущее количество скачиваний")

    def __repr__(self) -> str:
        """Строковое представление объекта ссылки"""
        return f'<ShareLink for file {self.file_id}>'

    def is_valid(self) -> bool:
        """Проверяет действительность ссылки"""
        if self.expiration and self.expiration < datetime.utcnow():
            return False
        if self.download_limit and self.download_count >= self.download_limit:
            return False
        return True