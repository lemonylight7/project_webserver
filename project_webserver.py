from flask import Flask, session, redirect, request, render_template, flash, jsonify
from flask_restful import reqparse, abort, Api, Resource
from datetime import datetime
from db import DB, PostsModel, UsersModel, LikesModel, CommentsModel, SubsModel
from project_forms import LoginForm, RegisterForm, UploadPhotoForm, ChangeInfoForm
from PIL import Image
import os

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

db = DB("project.db")

'''
---===###  Useful functions  ###===---
'''


def make_thumbnail(infile, outfile):
    im = Image.open(infile)
    xsize, ysize = im.size
    if xsize > ysize:
        crop_size = (xsize/2 - ysize/2, 0, xsize/2 + ysize/2, ysize)
    else:
        crop_size = (0, ysize/2 - xsize/2, xsize, ysize/2 + xsize/2)
    im = im.crop(box=crop_size)
    im.thumbnail((300, 300))
    im.save(outfile)


def save_file(f):
    save_filename = "static/img/usr_{0}/{1}_{2}".format(
        session['userid'], round(datetime.timestamp(datetime.now())), f.filename
    )
    thmb_filename = "static/img/usr_{0}/thmb/{1}_{2}".format(
        session['userid'], round(datetime.timestamp(datetime.now())), f.filename
    )
    os.makedirs('static/img/usr_{}'.format(session['userid']), exist_ok=True)
    os.makedirs('static/img/usr_{}/thmb'.format(session['userid']), exist_ok=True)
    f.save(save_filename)
    make_thumbnail(save_filename, thmb_filename)
    return (save_filename, thmb_filename)


def abort_if_post_not_found(post_id):
    if not PostsModel(db.get_connection()).get(post_id):
        abort(404, message="Post {} not found".format(post_id))


def abort_if_not_authorized():
    if "userid" not in session:
        abort(401, message="User is not authorized")


'''
---===###  API classes and bindings  ###===---
'''


class Posts(Resource):
    def get(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        # получаем одну запрошенную публикацию
        post = PostsModel(db.get_connection()).get(post_id)
        return jsonify({'post': post})

    def post(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        parser = reqparse.RequestParser()
        parser.add_argument('title')
        args = parser.parse_args()
        # изменияем описание на присланное в запросе post
        PostsModel(db.get_connection()).update_title(post_id, args['title'])
        return jsonify({'success': 'OK'})

    def delete(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        # удаляем публикацию
        PostsModel(db.get_connection()).delete(post_id)
        return jsonify({'success': 'OK'})

api.add_resource(Posts, '/api/posts/<int:post_id>')


class Likes(Resource):
    def get(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        # получаем количество лайков для данной публикации
        count = LikesModel(db.get_connection()).get_count(post_id)
        # проверяем есть ли твой лайк под данной публикацией
        your = LikesModel(db.get_connection()).get_your(post_id, session['userid'])
        return jsonify({'count': count, 'your': your})

    def post(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        # добавляем лайк
        LikesModel(db.get_connection()).insert(post_id, session['userid'])
        # получаем актуальное количество лайков
        count = LikesModel(db.get_connection()).get_count(post_id)
        return jsonify({'count': count})

    def delete(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        # удаляем лайк
        LikesModel(db.get_connection()).delete(post_id, session['userid'])
        # получаем актуальное количество лайков
        count = LikesModel(db.get_connection()).get_count(post_id)
        return jsonify({'count': count})

api.add_resource(Likes, '/api/likes/<int:post_id>')


class Comments(Resource):
    def get(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        # получаем данные для отображения описания и комментариев
        comments = CommentsModel(db.get_connection()).get(post_id)
        return jsonify({'comments': comments})

    def post(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        parser = reqparse.RequestParser()
        parser.add_argument('comment')
        args = parser.parse_args()
        # добавляем комментарий
        CommentsModel(db.get_connection()).insert(post_id, session['userid'], args['comment'])
        return jsonify({'success': 'OK'})

    def delete(self, post_id):
        abort_if_post_not_found(post_id)
        abort_if_not_authorized()
        parser = reqparse.RequestParser()
        parser.add_argument('comment_id')
        args = parser.parse_args()
        # удаляем комментарий
        CommentsModel(db.get_connection()).delete(args['comment_id'], session['userid'])
        return jsonify({'success': 'OK'})

api.add_resource(Comments, '/api/comments/<int:post_id>')


class Users(Resource):
    def get(self, user_id):
        abort_if_not_authorized()
        if user_id == 0:
            # поиск пользователя
            parser = reqparse.RequestParser()
            parser.add_argument('user_name')
            args = parser.parse_args()
            # получаем данные пользователя по имени
            user = UsersModel(db.get_connection()).get_by_name(args['user_name'])
            return jsonify({'user': user})
        else:
            # вывод статистики
            posts = PostsModel(db.get_connection())
            subs = SubsModel(db.get_connection())
            return jsonify({'followers_count': subs.get_followers(user_id),
                            'subscriptions_count': subs.get_subscriptions(user_id),
                            'posts_count': posts.get_count(user_id)})

    def post(self, user_id):
        abort_if_not_authorized()
        parser = reqparse.RequestParser()
        parser.add_argument('action')
        args = parser.parse_args()
        if args['action'] == 'subscribe':
            # подписываемся
            SubsModel(db.get_connection()).subscribe(session['userid'], user_id)
            next_act = 'unsubscribe'
            text = 'Отписаться'
        elif args['action'] == 'unsubscribe':
            # отписываемся
            SubsModel(db.get_connection()).unsubscribe(session['userid'], user_id)
            next_act = 'subscribe'
            text = 'Подписаться'
        return jsonify({'success': 'OK', 'next': next_act, 'text': text})

api.add_resource(Users, '/api/users/<int:user_id>')


'''
---===###  Flask URL handlers  ###===---
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    login_error = ''
    if form.validate_on_submit():
        users = UsersModel(db.get_connection())
        # проверяем существует ли пользователь с таким логином и паролем
        user = users.exists(form.username.data, form.password.data)
        if user[0]:
            # выставляем id пользователя в сессию
            session['userid'] = users.get(user[1])[0]
            return redirect('/')
        else:
            login_error = 'Неправильный логин или пароль'
    return render_template('project_login.html', title='Instagram', form=form,
                           login_error=login_error, user_info={'userid': 0})


@app.route('/')
def index():
    if "userid" not in session:
        return redirect('/login')
    posts = PostsModel(db.get_connection())
    all_posts = []
    for i in posts.get_all(session['userid']):
        all_posts.append({'pub_date': datetime.fromtimestamp(i[5]).strftime('%d.%m.%Y %H:%M'),
                         'title': i[1], 'thumb': i[3], 'userid': i[4], 'pid': i[0]})
    users = UsersModel(db.get_connection())
    subs = SubsModel(db.get_connection())
    user_data = users.get(session['userid'])
    user_info = {'username': user_data[1], 'main_photo': user_data[4],
                 'followers_count': subs.get_followers(session['userid']),
                 'subscriptions_count': subs.get_subscriptions(session['userid']),
                 'posts_count': posts.get_count(session['userid']), 'userid': session['userid']}
    return render_template('project_index.html', title='Instagram', posts=all_posts,
                           user_info=user_info, sess_info=user_info)


@app.route('/@<username>')
def user_page(username):
    if "userid" not in session:
        return redirect('/login')
    posts = PostsModel(db.get_connection())
    users = UsersModel(db.get_connection())
    subs = SubsModel(db.get_connection())
    userid = users.get_by_name(username)[0]
    all_posts = []
    for i in posts.get_all(userid):
        all_posts.append({'pub_date': datetime.fromtimestamp(i[5]).strftime('%d.%m.%Y %H:%M'),
                         'title': i[1], 'thumb': i[3], 'userid': i[4], 'pid': i[0]})
    user_data = users.get(userid)
    user_info = {'username': user_data[1], 'main_photo': user_data[4],
                 'subscribed': subs.check_subscribed(session['userid'], userid), 'userid': user_data[0]}
    user_data = users.get(session['userid'])
    sess_info = {'username': user_data[1], 'main_photo': user_data[4]}
    return render_template('project_index.html', title='Instagram',
                           posts=all_posts, user_info=user_info, sess_info=sess_info)


@app.route('/del_post/<pid>')
def del_post(pid):
    if "userid" not in session:
        return redirect('/login')
    posts = PostsModel(db.get_connection())
    post = posts.get(pid)
    if post[4] == session['userid']:
        posts.delete(pid)
    else:
        flash('Доступ запрещен', 'danger')
    return redirect('/')


@app.route('/registration', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        users = UsersModel(db.get_connection())
        if not users.get_by_name(form.username.data):
            users.insert(form.username.data, form.password.data)
            flash('Спасибо за регистрацию', 'success')
            return redirect('/login')
        else:
            form.username.errors.append('Пользователь с таким именем уже существует')
    return render_template('project_register.html', title='Instagram', form=form, user_info={'userid': 0})


@app.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    if "userid" not in session:
        return redirect('/login')
    form = UploadPhotoForm()
    if form.validate_on_submit():
        f = request.files['file']
        save_filename, thmb_filename = save_file(f)
        posts = PostsModel(db.get_connection())
        posts.insert(form.descrypt.data, save_filename, thmb_filename, session['userid'])
        return redirect('/')
    users = UsersModel(db.get_connection())
    user_data = users.get(session['userid'])
    user_info = {'username': user_data[1], 'main_photo': user_data[4]}
    return render_template('project_add_photos.html', form=form, user_info=user_info, sess_info=user_info)


@app.route('/change_info', methods=['GET', 'POST'])
def change_info():
    if "userid" not in session:
        return redirect('/login')
    form = ChangeInfoForm()
    keys = {'user_name': form.user_name.data, 'password_hash': form.password_hash.data}
    users = UsersModel(db.get_connection())
    if form.validate_on_submit():
        if not users.get_by_name(form.user_name.data):
            if form.main_photo.data != '':
                f = request.files['main_photo']
                save_filename, thmb_filename = save_file(f)
                users.update_user_info(session['userid'], 'main_photo', thmb_filename)
            for key in keys:
                if keys[key] != '':
                    users.update_user_info(session['userid'], key, keys[key])
            return redirect('/')
        else:
            form.username.errors.append('Пользователь с таким именем уже существует')
    user_data = users.get(session['userid'])
    user_info = {'username': user_data[1], 'main_photo': user_data[4]}
    return render_template('project_change_info.html', form=form, user_info=user_info, sess_info=user_info)


@app.route('/logout')
def logout():
    session.pop('userid', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
