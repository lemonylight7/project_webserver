from flask import Flask, session, redirect, request, render_template, flash, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from wtforms import StringField, BooleanField, SubmitField, TextAreaField, PasswordField, FileField
from wtforms.validators import DataRequired, EqualTo
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

class DB:
    def __init__(self, db_file):
        conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()

db = DB("project.db")

class NewsModel:
    def __init__(self, connection):
        self.connection = connection
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name='news'")
        row = cursor.fetchone()
        if row is None:
            self.init_table()

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS news
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             title VARCHAR(100),
                             photo TEXT,
                             user_id INTEGER,
                             pub_date INTEGER
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, photo, user_id):
        cursor = self.connection.cursor()
        pub_date = round(datetime.timestamp(datetime.now()))
        cursor.execute('''INSERT INTO news
                          (title, photo, user_id, pub_date)
                          VALUES (?,?,?,?)''', (title, photo, str(user_id), pub_date))
        cursor.close()
        self.connection.commit()

    def get(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ?", (str(news_id),))
        row = cursor.fetchone()
        return row

    def get_all(self, user_id=None, sort='0'):
        if sort == '0':
            order = ' ORDER BY pub_date DESC'
        else:
            order = ' ORDER BY title'
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM news WHERE user_id = ?" + order,
                           (str(user_id),))
        else:
            cursor.execute("SELECT * FROM news" + order)
        rows = cursor.fetchall()
        return rows

    def delete(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM news WHERE id = ?''', (str(news_id),))
        cursor.close()
        self.connection.commit()


class UsersModel:
    def __init__(self, connection):
        self.connection = connection
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name='users'")
        row = cursor.fetchone()
        if row is None:
            self.init_table()


    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128),
                             admin INTEGER,
                             main_photo TEXT
                             )''')
        cursor.execute('''INSERT INTO users (user_name, password_hash, admin, main_photo)
                          VALUES (?,?,?,?)''', ('ermakova', 'pass', 0, 'no_photo.png'))
        cursor.execute('''INSERT INTO users (user_name, password_hash, admin, main_photo)
                          VALUES (?,?,?,?)''', ('avokamre', 'ssap', 0, 'no_photo.png'))
        cursor.close()
        self.connection.commit()

    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users
                          (user_name, password_hash, admin, main_photo)
                          VALUES (?,?,?,?)''', (user_name, password_hash, 0, 'no_photo.png'))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        return row

    def get_by_name(self, user_name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ?", (user_name,))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class NewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')

class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(message='Поле не должно быть пустым')])
    password = PasswordField('Введите пароль', [DataRequired(message='Поле не должно быть пустым'),
        EqualTo('confirm', message='Пароли должны совпадать')])
    confirm = PasswordField('Повторите пароль', validators=[DataRequired(message='Поле не должно быть пустым')])
    submit = SubmitField('Зарегистрироваться')

class LoadPhotoForm(FlaskForm):
    photo = FileField('Загрузите фото')
    descrypt = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Загрузить')

@app.route('/login', methods=['GET', 'POST'])
def diaries_login():
    form = LoginForm()
    login_error = ''
    if form.validate_on_submit():
        users = UsersModel(db.get_connection())
        user = users.exists(form.username.data, form.password.data)
        if user[0]:
            session['userid'] = users.get(user[1])[0]
            session['username'] = users.get(user[1])[1]
            session['admin'] = users.get(user[1])[3]
            session['main_photo'] = url_for('static', filename='img/' + users.get(user[1])[4])
            print()
            session['sort'] = 0
            return redirect('/')
        else:
            login_error = 'Неправильный логин или пароль'
    return render_template('project_login.html', title='Личные дневники', form=form, login_error=login_error)

@app.route('/')
def diaries_index():
    if "username" not in session:
        return redirect('/login')
    news = NewsModel(db.get_connection())
    all_news = []
    for i in news.get_all(session['userid'], session['sort']):
        all_news.append({'pub_date': datetime.fromtimestamp(i[4]).strftime('%d.%m.%Y %H:%M'),
                         'title': i[1], 'photo': url_for('static', filename='img/' + i[2]), 'nid': i[0]})
    return render_template('project_index.html', title='Instagram', news=all_news)

@app.route('/del_news/<nid>')
def diaries_del_news(nid):
    if "username" not in session:
        return redirect('/login')
    news = NewsModel(db.get_connection())
    news.delete(nid)
    return redirect('/')

@app.route('/registration', methods=['GET', 'POST'])
def diaries_register():
    form = RegisterForm()
    if form.validate_on_submit():
        users = UsersModel(db.get_connection())
        users.insert(form.username.data, form.password.data)
        flash('Спасибо за регистрацию', 'success')
        return redirect('/login')
    return render_template('project_register.html', title='Личные дневники', form=form)

@app.route('/admin')
def diaries_admin():
    if "username" not in session or session['admin'] != 1:
        flash('Доступ запрещен', 'danger')
        return redirect('/')
    news = NewsModel(db.get_connection())
    all_news = news.get_all()
    users = UsersModel(db.get_connection())
    stats = {}
    usernames = {}
    for i in all_news:
        if i[3] in stats:
            stats[i[3]] += 1
        else:
            stats[i[3]] = 1
            usernames[i[3]] = users.get(i[3])[1]
    return render_template('project_admin.html', title='Статистика пользователей',
                           stats=stats, names=usernames)

@app.route('/sort/<sort>')
def change_sort(sort):
    if "username" not in session:
        return redirect('/login')
    session['sort'] = sort
    return redirect('/')

@app.route('/load_photo', methods=['GET', 'POST'])
def load_photo():
    if "username" not in session:
        return redirect('/login')
    form = LoadPhotoForm()
    if form.validate_on_submit():
        news = NewsModel(db.get_connection())
        print(form.descrypt.data)
        news.insert(form.descrypt.data, form.photo.data, session['userid'])
        return redirect('/')
    return render_template('project_add_photos.html', form=form)


@app.route('/logout')
def diaries_logout():
    session.pop('username', None)
    session.pop('userid', None)
    session.pop('admin', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
