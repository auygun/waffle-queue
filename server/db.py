import lazy_object_proxy
import pymysql


def _connect():
    print("db: Opening connection")
    return pymysql.connect(host='127.0.0.1', port=3306,
                           user='mysql', password='mysql',
                           db='builder', autocommit=False,
                           cursorclass=pymysql.cursors.DictCursor)


_conn = lazy_object_proxy.Proxy(_connect)


def ping():
    _conn.ping(reconnect=True)


def cursor():
    return _conn.cursor()


def commit():
    return _conn.commit()


def rollback():
    return _conn.rollback()


def now():
    with _conn.cursor() as cursor:
        cursor.execute("SELECT NOW()")
        return cursor.next()[0]
