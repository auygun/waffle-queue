import pymysql
from flask import g

import worker


def init_app(app):
    app.teardown_appcontext(close)


def connection():
    if '_conn' not in g:
        print("db: Opening connection")
        g._conn = pymysql.connect(host='127.0.0.1', port=3306,
                                  user='mysql', password='mysql',
                                  db='builder', autocommit=False,
                                  cursorclass=pymysql.cursors.DictCursor)
    return g._conn


def close(e=None):
    conn = g.pop('_conn', None)
    if conn is not None:
        print("db: Closing connection")
        conn.commit()
        conn.close()


def cursor():
    return connection().cursor()


def commit():
    return connection().commit()


def rollback():
    return connection().rollback()


def now():
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT NOW()")
            return cursor.next()[0]
