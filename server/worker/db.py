import lazy_object_proxy
import pymysql


def _connect():
    return pymysql.connect(host='127.0.0.1', port=3306,
                           user='mysql', password='mysql',
                           db='waffle_queue', autocommit=False)


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
    with _conn.cursor() as cur:
        cur.execute("SELECT NOW()")
        return cur.next()[0]
