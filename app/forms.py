from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import User
from datetime import timedelta

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(),
        Length(min=4, max=25)
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=8)
    ])
    confirm = PasswordField('Подтвердите пароль', validators=[  # Изменили имя поля
        DataRequired(),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Это имя пользователя уже занято')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class ShareSettingsForm(FlaskForm):
    expiration = SelectField('Срок действия', choices=[
        (3600, '1 час'),
        (86400, '24 часа'),
        (604800, '7 дней'),
        (2592000, '30 дней'),
        (0, 'Без ограничений')
    ], coerce=int, default=2592000)
    
    password = PasswordField('Пароль доступа')
    download_limit = IntegerField('Лимит скачиваний', render_kw={"placeholder": "0 - без ограничений"})
    enable_notifications = BooleanField('Уведомлять о скачиваниях')
    submit = SubmitField('Сохранить')