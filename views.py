# -*- encoding: utf8 -*-
import sqlalchemy.exc
from sqlalchemy.sql import text

from flask import render_template, request, flash, redirect, url_for, current_app
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user

from app import *
from models import *
from database import db_session, init_db, engine

login_manager = LoginManager(app)


def is_admin(func):
    def wrapper(*args, **kwargs):
        if current_user.role == RoleE.USER:
            return redirect('/')
        else:
            return func(*args, **kwargs)
    return wrapper

@login_manager.user_loader
def load_user(userid):
    return User.query.filter(User.id == userid).first()

@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/')
def indexs():
    return render_template('index.html')

@app.route('/threads')
def threads():
    sql = 'SELECT t.id, t.topic, u.login, p.add_time FROM threads t INNER JOIN posts p ON p.id = t.post_id INNER JOIN users u ON u.id = p.author_id ORDER BY p.add_time DESC'
    conn = engine.raw_connection()
    threads = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        threads = cursor.fetchall()
        if not threads:
            flash("Brak watkow")
    except:
        pass
    return render_template('thread_list.html', threads=threads)

@app.route('/thread/<int:id>')
@login_required
def thread(id):
    sql = 'SELECT t.topic, p.content, p.add_time, u.login, p.id FROM threads t INNER JOIN posts p ON p.id = t.post_id INNER JOIN users u ON u.id = p.author_id WHERE t.id=:thread_id'
    conn = engine.raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, { 'thread_id': id })
        thread_post = cursor.fetchone()
        if not thread_post:
            flash("podany watek nie istnieje lub zostal usuniety!")
    except:
        thread_post = None
    sql = 'SELECT p.content, p.add_time, u.login FROM posts p JOIN users u ON (u.id = p.author_id) WHERE p.parent_id=:parent_id ORDER BY p.add_time'
    try:
        cursor = conn.cursor()
        cursor.execute(sql, { 'parent_id': thread_post[4] })
        answers = cursor.fetchall()
        print answers
        if not answers:
            flash("Ten watek nie posiada jeszcze zadnych odpowiedzi")
    except Exception as e:
        print e
        answers = None
    return render_template('thread_show.html', thread=thread_post, answers=answers)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        u = User.query.filter(User.login == login).first()
        if u and u.check_password(password):
            login_user(u)
            return redirect('/')
        else:
            flash('Bledny login lub haslo')
    return render_template('login_form.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    template = render_template('register_form.html')
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        u = User(login, password)
        try:
            db_session.add(u)
            db_session.commit()
            return redirect(url_for('login'))
        except sqlalchemy.exc.IntegrityError as e:
            flash('Podany uzytkownik juz istnieje!')
    return template
@is_admin
@app.route('/admin/')
@login_required
def admin_dashboard():
    # ostatnie 10 postow
    sql = 'SELECT p.content, u.login, p.add_time FROM posts p INNER JOIN users u ON u.id = p.author_id ORDER BY p.add_time DESC  LIMIT 10 '
    conn = engine.raw_connection()
    try:
        cursor = conn.cursor()
        print sql
        cursor.execute(sql)
        last_ten_posts = cursor.fetchall()
    except:
        pass
    return render_template('admin_dashboard.html', last_ten_posts=last_ten_posts)

@app.route('/profile', defaults={'username': None})
@app.route('/profile/<username>')
@login_required
def show_user_profile(username):
    if not username:
        username = current_user.login
    # easy way
    # posts = Post.query.filter(Post.author_id == current_user.id).all()
    # hard way
    conn = engine.raw_connection()
    try:
        sql = 'SELECT count(p.id) FROM posts p INNER JOIN users u ON u.id = p.author_id WHERE u.login=:username'
        cursor = conn.cursor()
        print sql
        cursor.execute(sql, { 'username': username })
        result = cursor.fetchone()
        posts_count = result[0]
        sql = 'SELECT login, role FROM users WHERE login=:username'
        print sql
        cursor.execute(sql, { 'username': username })
        user = cursor.fetchone()
    except Exception as e:
        print e
        return redirect('/')

    return render_template('profile.html', posts_count=posts_count, username=user[0], is_admin=(user[1] == RoleE.ADMIN))

@app.route('/thread/new', methods=['GET', 'POST'])
@login_required
def new_thread():
    if request.method == 'POST':
        user = current_user
        data = request.form
        post = Post(None, user.id, data['content'])
        db_session.add(post)
        db_session.commit()
        th = Thread(data['topic'],post.id)
        db_session.add(th)
        db_session.commit()
        return redirect('/thread/%d' % th.id)
    else:
        return render_template('thread_form.html')



@app.route('/thread/answer/<int:post_id>', methods=['GET','POST'])
@login_required
def answer(post_id):
    if request.method == 'POST':
        data = request.form
        parent_id = post_id
        user = current_user
        post = Post(parent_id, user.id, data['content'])
        db_session.add(post)
        db_session.commit()
        if post.id:
            th = Thread.query.filter(Thread.post_id == post_id).first()
            return redirect('/thread/%d' % th.id)
    else:
        return render_template('thread_answer.html')

@is_admin
@app.route('/admin/users')
@login_required
def admin_list_users():
    sql = 'SELECT * FROM users'
    conn = engine.raw_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        users = cursor.fetchall()
    except:
        pass
    print users
    return render_template('admin_users_list.html', users=users)

@app.route('/set_me_as_admin')
@login_required
def set_me_as_admin():
    user = current_user
    current_user.role = RoleE.ADMIN
    sql = 'UPDATE users SET role=%d WHERE id=%d' % (RoleE.ADMIN, user.id)
    try:
        db_session.execute(sql)
        db_session.commit()
        print sql
    except Exception as e:
        print e
    return redirect('/admin')


@app.route('/admin/setadmin/<int:user_id>/<int:current_role>',methods=['GET','POST'], endpoint='set_admin')
@login_required
@is_admin
def admin_set_admin(user_id, current_role):
    if request.method == 'POST':
        try:
            user_new_role = RoleE.USER if (current_role == RoleE.ADMIN) else RoleE.ADMIN
            sql = 'UPDATE users SET role=:new_role WHERE id=:user_id'
            db_session.execute(sql, {'new_role' : user_new_role, 'user_id': user_id})
            db_session.commit()
        except Exception as e:
            print e
        return redirect('/admin/users?success')
    return redirect('/admin/users?fail')

@app.route('/admin/thread/remove/<int:thread_id>', methods=['GET'])
@login_required
@is_admin
def admin_remove_thread(thread_id):
    try:
        sql = 'SELECT post_id FROM threads WHERE id = :thread_id'
        results = db_session.execute(sql, {'thread_id': thread_id})
        post_id = list(list(results)[0])[0]
        sql = 'DELETE FROM posts WHERE parent_id = :post_id OR id = :post_id'
        db_session.execute(sql, {'post_id': post_id})
        sql = 'DELETE FROM threads WHERE id = :thread_id'
        db_session.execute(sql, {'thread_id': thread_id})
        db_session.commit()
    except Exception as e:
        print e
    return redirect('/threads')


@app.route('/init_db')
def init_database():
    init_db()
    return "Done!"
