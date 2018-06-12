import logging

import jwt
from flask import Flask, g, request, abort, flash, render_template, session, redirect, url_for
from flaskext.mysql import MySQL
from flask_httpauth import HTTPBasicAuth
from passlib import pwd
from passlib.hash import argon2

log = logging.getLogger(__name__)
app = Flask(__name__, template_folder='./templates')
mysql = MySQL(app)
auth = HTTPBasicAuth()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'project1-web'
app.config['MYSQL_DATABASE_PASSWORD'] = 'webpassword'
app.config['MYSQL_DATABASE_DB'] = 'project1'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

# session config
app.secret_key = pwd.genword(entropy=128)


def get_data(sql, params=None):
    conn = mysql.connect()
    cursor = conn.cursor()
    records = []

    try:
        log.debug(sql)
        cursor.execute(sql, params)
        result = cursor.fetchall()
        for row in result:
            records.append(list(row))

    except Exception as e:
        log.exception("Fout bij het ophalen van data: {0})".format(e))

    cursor.close()
    conn.close()

    return records


def set_data(sql, params=None):
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        log.debug(sql)
        cursor.execute(sql, params)
        conn.commit()
        log.debug("SQL uitgevoerd")

    except Exception as e:
        log.exception("Fout bij uitvoeren van sql: {0})".format(e))
        return False

    cursor.close()
    conn.close()

    return True


def add_user(user, password):
    try:
        if get_data('SELECT phcstring FROM project1.users WHERE userid=%s', (user,)):
            message = 'User {} exists!'.format(user)
            log.info(message)
            return False, message

        argon_hash = argon2.hash(password)
        if set_data('INSERT INTO project1.users (userid, phcstring) VALUES (%s, %s);', (user, argon_hash)):
            message = 'Added user {}'.format(user)
            log.info(message)
            return True, message

    except Exception as e:
        message = 'Error adding user {}: {}'.format(user, e)
        log.error(message)
        return False, message


def decode_token():
    token = session.get('auth_token')
    if token:
        try:
            return jwt.decode(token, app.secret_key)
        except Exception as e:
            log.exception(e)
            return None


@auth.verify_password
def verify_credentials(login, password):
    if decode_token():
        log.debug("Authenticated by token")
        return True
    record = get_data('SELECT phcstring FROM project1.users WHERE userid=%s', (login,))
    if not record:
        return False
    authorized = argon2.verify(password, record[0][0])
    if authorized:
        session['auth_token'] = jwt.encode(
            {'user': login},
            app.secret_key,
        )
        # g.user = login
    return authorized


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/secure')
@auth.login_required
def secure():
    auth_data = decode_token()
    if not auth_data:
        abort(403)
    return 'Hello, {}!'.format(auth_data.get('user'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        if not user and password:
            abort(400)
        if verify_credentials(user, password):
            return redirect(url_for('secure'))
        flash("Authentication failed")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    result = None
    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')
        if not user and password:
            abort(400)
        result, message = add_user(user, password)
        flash(message)
    return render_template('register.html', success=result)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    log.info("Flask app starting")
    app.run(host='0.0.0.0', debug=True)
