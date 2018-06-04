import logging

from flask import Flask, g, request, abort, flash, render_template
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


def add_user(login, password):
    try:
        if get_data('SELECT phcstring FROM project1.users WHERE userid=%s', (login,)):
            message = 'User {} exists!'.format(login)
            log.info(message)
            return False, message

        argon_hash = argon2.hash(password)
        if set_data('INSERT INTO project1.users (userid, phcstring) VALUES (%s, %s);', (login, argon_hash)):
            message = 'Added user {}'.format(login)
            log.info(message)
            return True, message

    except Exception as e:
        message = 'Error adding user {}: {}'.format(login, e)
        log.error(message)
        return False, message


@auth.verify_password
def verify_credentials(login, password):
    record = get_data('SELECT phcstring FROM project1.users WHERE userid=%s', (login,))
    if not record:
        return False
    authorized = argon2.verify(password, record[0][0])
    if authorized:
        g.user = login
    return authorized


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/secure')
@auth.login_required
def secure():
    return 'Hello, {}!'.format(g.user)


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
