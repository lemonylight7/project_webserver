from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, FileField
from wtforms.validators import DataRequired, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(message='Поле не должно быть пустым')])
    password = PasswordField('Введите пароль', [DataRequired(message='Поле не должно быть пустым'),
        EqualTo('confirm', message='Пароли должны совпадать')])
    confirm = PasswordField('Повторите пароль', validators=[DataRequired(message='Поле не должно быть пустым')])
    submit = SubmitField('Зарегистрироваться')

class UploadPhotoForm(FlaskForm):
    file = FileField('Загрузите фото', validators=[FileRequired(message='Поле не должно быть пустым')])
    descrypt = TextAreaField('Описание')
    submit = SubmitField('Загрузить')
