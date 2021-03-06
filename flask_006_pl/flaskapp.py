import datetime
import os
import sqlite3

from flask import Flask, render_template, url_for, request, flash, get_flashed_messages, g, abort, session, redirect, \
    make_response

from flask_006_pl.flask_database import FlaskDataBase
from werkzeug.security import generate_password_hash, check_password_hash

from flask_006_pl.helpers import check_ext, check_password

DATABASE = 'flaskapp.db'
DEBUG = True
SECRET_KEY = 'gheghgj3qhgt4q$#^#$he'
MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # 3 MB

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flaskapp.db')))

app.permanent_session_lifetime = datetime.timedelta(days=1)


def create_db():
    """Creates new database from sql file."""
    db = connect_db()
    with app.open_resource('db_schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def connect_db():
    """Returns connection to apps database."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


url_menu_items = {
    'index': 'Главная',
    'second': 'Вторая страница'
}


@app.before_first_request
def before_first_request_func():
    print('BEFORE FIRST REQUEST called!')


fdb = None


@app.before_request
def before_request_func():
    global fdb
    fdb = FlaskDataBase(get_db())
    print('BEFORE REQUEST called!')


@app.after_request
def after_request_func(response):
    print('AFTER REQUEST called!')
    return response


@app.teardown_request
def teardown_request_func(response):
    print('TEARDOWN REQUEST called!')
    return response


@app.route('/')
def index():
    if 'username' in session:
        return render_template(
            'index.html',
            menu_url=fdb.get_menu(),
            posts=fdb.get_posts(),
            username=session.get('username').split('@')[0]
        )
    return render_template(
        'index.html',
        menu_url=fdb.get_menu(),
        posts=fdb.get_posts()
    )


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    email = ''
    password = ''

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if 'username' in session:
            flash('Вы уже зарегистрированы', category='error')
        elif not email:
            flash('Email не указан!', category='unfilled_error')
        elif '@' not in email or '.' not in email:
            flash('Некорректный email!', category='validation_error')
        elif not password:
            flash('Пароль не указан!', category='unfilled_error')
        else:
            password_errors = check_password(password)
            if password_errors['password_ok']:
                res = fdb.signup(email, generate_password_hash(password))
                if not res:
                    flash('User was not signed up. Unexpected error', category='error')
                else:
                    flash('Successful signing up', category='success')
                    return redirect(url_for('index'))
            else:
                for error in password_errors.keys():
                    if password_errors[error]:
                        flash(error, category='validation_error')
                        break
        return render_template('signup.html',
                               menu_url=fdb.get_menu(),
                               email_value=email,
                               password_value=password)
    return render_template('signup.html',
                           menu_url=fdb.get_menu(),
                           email_value=email,
                           password_value=password)


@app.route('/login', methods=['POST', 'GET'])
def login():
    email = ''
    password = ''
    if request.method == 'GET':
        return render_template('login.html',
                               menu_url=fdb.get_menu(),
                               email_value=email,
                               password_value=password)
    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email:
            flash('Email не указан!', category='unfilled_error')
        elif '@' not in email or '.' not in email:
            flash('Некорректный email!', category='validation_error')
        elif not password:
            flash('Пароль не указан!', category='unfilled_error')
        else:
            proper_password_hash = fdb.login(email)
            if check_password_hash(proper_password_hash, password):
                session['username'] = email
                return redirect(url_for('index'))
        flash('Неправильные данные аккаунта!', category='validation_error')
        return render_template('login.html',
                               menu_url=fdb.get_menu(),
                               email_value=email,
                               password_value=password)
    else:
        raise Exception(f'Method {request.method} not allowed')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/second')
def second():
    print(url_for('second'))
    print(url_for('index'))

    return render_template(
        'second.html',
        phone='+79172345678',
        email='myemail@gmail.com',
        current_date=datetime.date.today().strftime('%d.%m.%Y'),
        menu_url=fdb.get_menu()
    )


# int, float, path
@app.route('/user/<username>')
def profile(username):
    return f"<h1>Hello, {username.split('@')[0]}!</h1>"


@app.route('/add_post', methods=["GET", "POST"])
def add_post():
    if request.method == "POST":
        name = request.form["name"]
        post_content = request.form["post"]
        file = request.files.get('file')
        if len(name) > 5 and len(post_content) > 10:
            if file and check_ext(file.filename):
                try:
                    img = file.read()
                except FileNotFoundError:
                    flash('Ошибка чтения файла', category='error')
                    img = None
            res = fdb.add_post(name, post_content, img)
            if not res:
                flash('Post were not added. Unexpected error', category='error')
            else:
                flash('Success!', category='success')
        else:
            flash('Post name or content too small', category='error')
    return render_template('add_post.html', menu_url=fdb.get_menu())


@app.route('/post/<int:post_id>')
def post_content(post_id):
    title, content = fdb.get_post_content(post_id)
    if not title:
        abort(404)
    return render_template('post.html', menu_url=fdb.get_menu(), title=title, content=content)


@app.route('/photo/<int:post_id>')
def post_photo(post_id):
    photo = fdb.get_post_photo(post_id)
    response = make_response(photo)
    response.headers['Content-Type'] = 'image/png'
    return response


@app.route('/ajax')
def ajax_example():
    value = request.args['data']['value']
    return value + 1


@app.errorhandler(404)
def page_not_found(error):
    return "<h1>Oooops! This post doesn't exist</h1>"


@app.teardown_appcontext
def close_db(error):
    """Closes database connection if it exists."""
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route('/test_response1')
def test_response():
    content = render_template(
        'index.html',
        menu_url=fdb.get_menu(),
        posts=fdb.get_posts()
    )
    response_obj = make_response(content)
    response_obj.headers['Content-type'] = 'text/plain'
    return response_obj


@app.route('/test_response2')
def test_response2():
    return "<h1>Test response 2 page</h1>", 404, {'Content-type': 'text/plain'}


@app.route('/redirect')
def redirect_example():
    return redirect(url_for('index'))


@app.route('/test_login')
def test_login():
    log = ''
    if request.cookies.get('visited'):
        log = request.cookies.get('visited')

    response = make_response(f'<h1>Visited cookie: {log}</h1>')
    response.set_cookie('visited', 'yes')
    return response


@app.route('/test_login1')
def test_login1():
    log = ''
    if request.cookies.get('visited'):
        log = request.cookies.get('visited')

    response = make_response(f'<h1>Visited cookie: {log}</h1>')
    # response.set_cookie('visited', 'yes', expires=0)
    response.delete_cookie('visited')
    return response


@app.route('/session_example')
def session_example():
    if 'visits' in session:
        session['visits'] += 1
    else:
        session['visits'] = 1
    return f"<h1>Number of visits: {session['visits']}</h1>"


@app.route('/session_example2')
def session_example2():
    counter = session.get('visits', 1)
    session['visits'] = counter + 1
    return f"<h1>Number of visits: {session['visits']}</h1>"


data = [1, 2, 3]


@app.route('/session_example3')
def session_example3():
    session.permanent = True
    if 'data' not in session:
        session['data'] = data
    else:
        session['data'][0] += 1  # ссылка та же, поэтому flask не меняет значение
        session.modified = True
    return f'<h1>Data: {session["data"]}</h1>'


@app.route('/hash_example')
def hash_example():
    password = "Password1"
    hash = generate_password_hash(password)  # to sign up
    print(check_password_hash(hash, "Password1"))  # to sign in
    return f'<h1>Hash: {hash}</h1>'


if __name__ == '__main__':
    app.run(debug=True)
